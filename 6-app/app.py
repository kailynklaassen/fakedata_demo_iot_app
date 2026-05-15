"""
Utility Operations Intelligence Assistant — FastAPI backend.

Serves the static UI and proxies user questions to the multi-agent
supervisor model serving endpoint (Responses API), parsing the rich
tool-call / sub-agent trace into a UI-friendly shape.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
import uuid
from collections import OrderedDict
from pathlib import Path
from typing import Any

import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from databricks.sdk import WorkspaceClient

ENDPOINT_NAME = os.environ.get("SUPERVISOR_ENDPOINT", "mas-cf2369f5-endpoint")
STATIC_DIR = Path(__file__).parent / "static"

# In-memory job store. Single-replica deployment — fine for demo.
_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()
_JOB_TTL_SECONDS = 600  # 10 min

# Recent Q&A cache to skip the supervisor for repeated questions.
# Bounded LRU keyed by the (history + question) hash.
_qa_cache: "OrderedDict[str, tuple[float, dict]]" = OrderedDict()
_qa_lock = threading.Lock()
_QA_TTL_SECONDS = 3600  # 1 hour
_QA_MAX_ENTRIES = 100


def _gc_jobs():
    cutoff = time.time() - _JOB_TTL_SECONDS
    with _jobs_lock:
        stale = [k for k, v in _jobs.items() if v.get("created", 0) < cutoff]
        for k in stale:
            _jobs.pop(k, None)


def _cache_key(message: str, history: list[dict]) -> str:
    """Stable hash of the question + user-turn history (assistant turns excluded to avoid drift)."""
    user_turns = [h.get("content", "") for h in (history or []) if h.get("role") == "user"]
    blob = json.dumps([*user_turns, message.strip()], sort_keys=False)
    return hashlib.sha256(blob.encode()).hexdigest()


def _cache_get(key: str) -> dict | None:
    with _qa_lock:
        entry = _qa_cache.get(key)
        if not entry:
            return None
        ts, payload = entry
        if time.time() - ts > _QA_TTL_SECONDS:
            _qa_cache.pop(key, None)
            return None
        _qa_cache.move_to_end(key)
        return payload


def _cache_put(key: str, payload: dict) -> None:
    with _qa_lock:
        _qa_cache[key] = (time.time(), payload)
        _qa_cache.move_to_end(key)
        while len(_qa_cache) > _QA_MAX_ENTRIES:
            _qa_cache.popitem(last=False)

# Map Genie space IDs to friendly names so the UI can label them
GENIE_SPACE_LABELS = {
    "01f14f36fccd1c1198894bf8ba60a122": "Grid Operations",
    "01f14f3701fd12449af247f3739cca6e": "Financial Performance",
    "01f14f37062d1816ab94dc1f38edb3dc": "Maintenance & Workforce",
}

app = FastAPI(title="Utility Operations Intelligence Assistant")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
w = WorkspaceClient()


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/healthz")
def healthz():
    return {"ok": True, "endpoint": ENDPOINT_NAME}


def _classify_tool(name: str) -> dict:
    """Identify which kind of source a tool call hits."""
    if not name:
        return {"kind": "tool", "label": "Tool", "id": None}
    if name.startswith("genie-"):
        space_id = name.removeprefix("genie-")
        label = GENIE_SPACE_LABELS.get(space_id, "Genie Space")
        return {"kind": "genie", "label": label, "id": space_id}
    if "knowledge" in name.lower() or "rag" in name.lower() or "doc" in name.lower() or "retriev" in name.lower() or "vector" in name.lower():
        return {"kind": "rag", "label": "Utility Ops Knowledge", "id": name}
    return {"kind": "tool", "label": name, "id": name}


def _text_from_content(content) -> str:
    """Pull plain text out of a content array (list of {type, text} dicts)."""
    if not isinstance(content, list):
        return str(content or "")
    parts = []
    for c in content:
        if isinstance(c, dict) and c.get("type") == "output_text":
            parts.append(c.get("text", ""))
        elif isinstance(c, dict) and "text" in c:
            parts.append(c.get("text", ""))
    return "".join(parts)


HANDOFF_RE = re.compile(r"<name>([^<]+)</name>", re.IGNORECASE)


def parse_response(resp: dict) -> dict:
    """Convert the Agent Responses API output into our UI schema."""
    output = resp.get("output") or []
    trace: list[dict] = []
    sources: list[dict] = []
    seen_source_keys: set[str] = set()
    final_answer = ""

    pending_call: dict | None = None  # match function_call → next tool result message

    for item in output:
        itype = item.get("type")
        if itype == "function_call":
            tool_info = _classify_tool(item.get("name", ""))
            args = item.get("arguments") or "{}"
            try:
                args_parsed = json.loads(args) if isinstance(args, str) else args
            except Exception:
                args_parsed = {"raw": args}
            entry = {
                "step": "tool_call",
                "label": f"Routed to {tool_info['label']}",
                "tool_kind": tool_info["kind"],
                "tool_name": item.get("name"),
                "tool_id": tool_info["id"],
                "tool_label": tool_info["label"],
                "args": args_parsed,
                "call_id": item.get("call_id"),
            }
            trace.append(entry)
            pending_call = entry
            key = f"{tool_info['kind']}:{tool_info['id'] or tool_info['label']}"
            if key not in seen_source_keys:
                seen_source_keys.add(key)
                sources.append({
                    "kind": tool_info["kind"],
                    "label": tool_info["label"],
                    "id": tool_info["id"],
                })

        elif itype == "message":
            text = _text_from_content(item.get("content"))
            # Skip empty / pure handoff tokens
            handoff = HANDOFF_RE.search(text)
            stripped = HANDOFF_RE.sub("", text).strip()

            if pending_call is not None and item.get("call_id") == pending_call.get("call_id"):
                trace.append({
                    "step": "tool_result",
                    "label": f"Received from {pending_call['tool_label']}",
                    "tool_kind": pending_call["tool_kind"],
                    "result": stripped or text,
                    "call_id": item.get("call_id"),
                })
                pending_call = None
                continue

            if handoff:
                # Sub-agent handoff signal (e.g., <name>supervisor-agent-operations</name>)
                agent = handoff.group(1)
                # Strip the "genie-<uuid>" handoffs because we already record those as tool_calls
                if not agent.startswith("genie-"):
                    trace.append({
                        "step": "handoff",
                        "label": f"Active agent: {agent}",
                        "agent": agent,
                    })
                if stripped:
                    # if there's also message text alongside handoff, treat as assistant
                    trace.append({"step": "assistant_text", "label": "Reasoning", "text": stripped})
                    final_answer = stripped
                continue

            if stripped:
                trace.append({"step": "assistant_text", "label": "Reasoning", "text": stripped})
                final_answer = stripped  # keep the last assistant message as the final answer

    return {
        "answer": final_answer or "(no response)",
        "trace": trace,
        "sources": sources,
        "raw_status": resp.get("status"),
        "response_id": resp.get("id"),
    }


def _build_partial_trace(output_items: list[dict]) -> tuple[list[dict], list[dict]]:
    """Build a UI-friendly trace + sources list from the output items seen so far.
    Mirrors parse_response() but is safe to call mid-stream."""
    trace: list[dict] = []
    sources: list[dict] = []
    seen: set[str] = set()
    pending_call: dict | None = None
    for item in output_items:
        itype = item.get("type")
        if itype == "function_call":
            ti = _classify_tool(item.get("name", ""))
            try:
                args = json.loads(item.get("arguments") or "{}") if isinstance(item.get("arguments"), str) else (item.get("arguments") or {})
            except Exception:
                args = {"raw": item.get("arguments")}
            entry = {
                "step": "tool_call",
                "label": f"Routed to {ti['label']}",
                "tool_kind": ti["kind"], "tool_name": item.get("name"),
                "tool_id": ti["id"], "tool_label": ti["label"],
                "args": args, "call_id": item.get("call_id"),
            }
            trace.append(entry)
            pending_call = entry
            k = f"{ti['kind']}:{ti['id'] or ti['label']}"
            if k not in seen:
                seen.add(k)
                sources.append({"kind": ti["kind"], "label": ti["label"], "id": ti["id"]})
        elif itype == "message":
            text = _text_from_content(item.get("content"))
            handoff = HANDOFF_RE.search(text)
            stripped = HANDOFF_RE.sub("", text).strip()
            if pending_call is not None and item.get("call_id") == pending_call.get("call_id"):
                trace.append({
                    "step": "tool_result",
                    "label": f"Received from {pending_call['tool_label']}",
                    "tool_kind": pending_call["tool_kind"],
                    "result": stripped or text,
                    "call_id": item.get("call_id"),
                })
                pending_call = None
                continue
            if handoff and not handoff.group(1).startswith("genie-"):
                trace.append({"step": "handoff", "label": f"Active agent: {handoff.group(1)}", "agent": handoff.group(1)})
            if stripped:
                trace.append({"step": "assistant_text", "label": "Reasoning", "text": stripped})
    return trace, sources


def _run_supervisor_job(job_id: str, input_messages: list[dict]) -> None:
    """Background worker — streams events from the supervisor endpoint and
    updates the job state with partial answer + trace as they arrive."""
    t0 = time.time()
    cfg = w.config
    try:
        auth_headers = cfg.authenticate()
    except Exception as e:
        with _jobs_lock:
            _jobs[job_id]["status"] = "error"
            _jobs[job_id]["error"] = f"auth error: {e}"
        return

    url = f"{cfg.host.rstrip('/')}/serving-endpoints/{ENDPOINT_NAME}/invocations"
    headers = {**auth_headers, "Content-Type": "application/json", "Accept": "text/event-stream"}
    body = {"input": input_messages, "stream": True}

    output_items: list[dict] = []  # completed output items (for trace)
    text_by_item: dict[str, str] = {}  # incremental text deltas per item_id
    last_item_id: str | None = None
    final_response_payload: dict | None = None

    try:
        with requests.post(url, headers=headers, json=body, stream=True, timeout=600) as r:
            if r.status_code >= 400:
                err_body = r.text[:500]
                with _jobs_lock:
                    _jobs[job_id]["status"] = "error"
                    _jobs[job_id]["error"] = f"upstream HTTP {r.status_code}: {err_body}"
                return
            buf = b""
            for chunk in r.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    line = line.strip()
                    if not line or not line.startswith(b"data:"):
                        continue
                    payload = line[5:].lstrip()
                    if payload in (b"[DONE]", b""):
                        continue
                    try:
                        evt = json.loads(payload.decode("utf-8"))
                    except Exception:
                        continue
                    etype = evt.get("type", "")

                    if etype == "response.output_text.delta":
                        iid = evt.get("item_id") or "_unknown"
                        delta = evt.get("delta", "")
                        text_by_item.setdefault(iid, "")
                        text_by_item[iid] += delta
                        last_item_id = iid
                        with _jobs_lock:
                            _jobs[job_id]["partial_answer"] = text_by_item[iid]
                    elif etype in ("response.output_item.done", "response.output_item.added"):
                        item = evt.get("item") or evt.get("output_item") or {}
                        if item and etype == "response.output_item.done":
                            output_items.append(item)
                            trace, sources = _build_partial_trace(output_items)
                            with _jobs_lock:
                                _jobs[job_id]["partial_trace"] = trace
                                _jobs[job_id]["partial_sources"] = sources
                    elif etype in ("response.completed", "response.done"):
                        final_response_payload = evt.get("response") or evt

    except requests.exceptions.RequestException as e:
        with _jobs_lock:
            _jobs[job_id]["status"] = "error"
            _jobs[job_id]["error"] = f"stream error: {e}"
        return

    # Synthesize the final payload. Prefer the explicit `response.completed` if we got it.
    if final_response_payload and isinstance(final_response_payload.get("output"), list):
        data = final_response_payload
    else:
        data = {"output": output_items, "status": "completed"}

    parsed = parse_response(data)
    if not parsed.get("answer") and last_item_id and text_by_item.get(last_item_id):
        parsed["answer"] = text_by_item[last_item_id]
    parsed["elapsed_ms"] = int((time.time() - t0) * 1000)

    with _jobs_lock:
        _jobs[job_id]["status"] = "done"
        _jobs[job_id]["result"] = parsed


@app.post("/api/chat")
def chat(req: ChatRequest):
    """Kick off a supervisor call as a background job. Returns immediately with job_id.

    Cache hit short-circuit: if we've seen the same (history + question) within the TTL,
    we create a job pre-populated with the cached result so the frontend's normal poll
    loop just sees `done` on the first poll.
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="empty message")
    _gc_jobs()
    input_messages = []
    for h in req.history:
        role = h.get("role")
        content = h.get("content", "")
        if role in ("user", "assistant") and content:
            input_messages.append({"role": role, "content": content})
    input_messages.append({"role": "user", "content": req.message})

    job_id = uuid.uuid4().hex
    cache_key = _cache_key(req.message, req.history)
    cached = _cache_get(cache_key)
    with _jobs_lock:
        if cached is not None:
            cached_with_flag = {**cached, "cached": True}
            _jobs[job_id] = {
                "status": "done", "created": time.time(),
                "result": cached_with_flag, "error": None,
            }
            return {"job_id": job_id, "status": "done", "cached": True}
        _jobs[job_id] = {
            "status": "running", "created": time.time(),
            "result": None, "error": None,
            "partial_answer": "", "partial_trace": [], "partial_sources": [],
            "cache_key": cache_key,
        }

    threading.Thread(
        target=_run_and_cache,
        args=(job_id, input_messages, cache_key),
        daemon=True,
        name=f"chat-{job_id[:8]}",
    ).start()

    return {"job_id": job_id, "status": "running"}


def _run_and_cache(job_id: str, input_messages: list[dict], cache_key: str) -> None:
    _run_supervisor_job(job_id, input_messages)
    # On success, cache the result
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job and job.get("status") == "done" and job.get("result"):
            _cache_put(cache_key, job["result"])


@app.get("/api/chat/{job_id}")
def chat_status(job_id: str):
    """Poll endpoint. Returns current status + partial streaming state while running,
    or the full result when done."""
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="job not found or expired")
        snap = {
            "status": job["status"],
            "elapsed_seconds": int(time.time() - job["created"]),
        }
        if job["status"] == "running":
            snap["partial_answer"] = job.get("partial_answer", "")
            snap["partial_trace"] = job.get("partial_trace", [])
            snap["partial_sources"] = job.get("partial_sources", [])
        elif job["status"] == "done":
            snap["result"] = job["result"]
        elif job["status"] == "error":
            snap["error"] = job["error"]
    return snap


@app.post("/api/cache/clear")
def cache_clear():
    with _qa_lock:
        n = len(_qa_cache)
        _qa_cache.clear()
    return {"cleared": n}
