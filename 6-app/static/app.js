// Operations Intelligence Assistant — frontend logic
// Wires the composer to /api/chat, renders messages, and populates the trace/sources panel.

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const messagesEl = $("#messages");
const composerEl = $("#composerInput");
const sendBtn = $("#sendBtn");
const newChatBtn = $("#newChatBtn");
const traceSection = $("#traceSection");
const sourcesSection = $("#sourcesSection");
const sourceList = $("#sourceList");
const convoTitle = $("#convoTitle");
const convoMeta = $("#convoMeta");
const recentList = $("#recentList");

let history = [];
let recentConversations = [];

function escapeHTML(s) {
  return (s ?? "").toString().replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

// Convert markdown-ish text to safe HTML.
// Supports: **bold**, *italic*, `code`, [text](url), bullets, headings, line breaks.
function renderMarkdown(text) {
  if (!text) return "";
  let s = escapeHTML(text);
  // Headings
  s = s.replace(/^### (.+)$/gm, "<h4 style='margin:10px 0 4px;font-size:13px;'>$1</h4>");
  s = s.replace(/^## (.+)$/gm, "<h3 style='margin:12px 0 6px;font-size:14px;'>$1</h3>");
  // Tables (very light)
  // Bold / italic / code
  s = s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  s = s.replace(/(^|[^*])\*([^*]+)\*([^*]|$)/g, "$1<em>$2</em>$3");
  s = s.replace(/`([^`]+)`/g, "<code style='background:var(--nx-gray-100);padding:1px 5px;border-radius:4px;font-size:12px;'>$1</code>");
  // Links
  s = s.replace(/\[([^\]]+)\]\(([^)]+)\)/g, "<a href='$2' target='_blank' rel='noopener' style='color:var(--nx-blue-dark);'>$1</a>");
  // Bullet lists
  s = s.replace(/^[ ]*[-*] (.+)$/gm, "<li>$1</li>");
  s = s.replace(/(<li>[\s\S]*?<\/li>(\n|$))+/g, (m) => `<ul style='margin:6px 0 6px 18px;'>${m}</ul>`);
  // Numbered lists
  s = s.replace(/^\s*\d+\.\s+(.+)$/gm, "<li>$1</li>");
  // Line breaks
  s = s.replace(/\n{2,}/g, "<br/><br/>");
  s = s.replace(/\n/g, "<br/>");
  return s;
}

function clearEmptyState() {
  const empty = messagesEl.querySelector(".empty-state");
  if (empty) empty.remove();
}

function appendUserMessage(text) {
  clearEmptyState();
  const div = document.createElement("div");
  div.className = "message user";
  div.innerHTML = `
    <div class="msg-avatar user">U</div>
    <div class="msg-content">${escapeHTML(text)}</div>
  `;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function appendThinkingMessage() {
  const div = document.createElement("div");
  div.className = "message assistant thinking-msg";
  div.innerHTML = `
    <div class="msg-avatar assistant">NX</div>
    <div class="msg-content">
      <div class="typing">
        <span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>
        <span>Supervisor is routing…</span>
      </div>
    </div>
  `;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return div;
}

function appendAssistantMessage(answer, sources, elapsed_ms, cached) {
  const pills = (sources || []).map(s => {
    const cls = s.kind === "rag" ? "rag" : (s.kind === "genie" ? "genie" : "tool");
    const icon = s.kind === "rag" ? "📄" : s.kind === "genie" ? "⚡" : "🔧";
    return `<span class="routing-pill ${cls}">${icon} ${escapeHTML(s.label)}</span>`;
  }).join("");

  const cachedBadge = cached ? `<span class="routing-pill" style="background:#FEF3C7;color:#92400E;border-color:#FDE68A;">⚡ Cached</span>` : "";
  const elapsedStr = elapsed_ms ? `<span style="font-size:11px;color:var(--nx-gray-500);margin-left:6px;">· ${(elapsed_ms/1000).toFixed(1)}s</span>` : "";

  const div = document.createElement("div");
  div.className = "message assistant";
  div.innerHTML = `
    <div class="msg-avatar assistant">NX</div>
    <div class="msg-content">
      <div class="routing-row">${cachedBadge}${pills}${elapsedStr}</div>
      <div class="md-body">${renderMarkdown(answer)}</div>
    </div>
  `;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function renderTrace(trace, elapsed_ms) {
  traceSection.innerHTML = "<h4>Supervisor Trace</h4>";
  if (!trace || trace.length === 0) {
    traceSection.innerHTML += '<div class="inspector-empty">No tool calls — supervisor answered directly.</div>';
    return;
  }
  trace.forEach((step, i) => {
    let cls = "trace-step done";
    let label = step.label || step.step;
    let detail = "";

    if (step.step === "tool_call") {
      cls = "trace-step tool-call " + (step.tool_kind === "rag" ? "rag" : "");
      detail = step.args ? `<div class="trace-detail code">${escapeHTML(JSON.stringify(step.args, null, 2))}</div>` : "";
    } else if (step.step === "tool_result") {
      cls = "trace-step tool-result";
      const txt = (step.result || "").toString();
      const preview = txt.length > 240 ? txt.slice(0, 240) + "…" : txt;
      detail = `<div class="trace-detail">${escapeHTML(preview)}</div>`;
    } else if (step.step === "handoff") {
      cls = "trace-step handoff";
      detail = `<div class="trace-detail">${escapeHTML(step.agent || "")}</div>`;
    } else if (step.step === "assistant_text") {
      cls = "trace-step done";
      const txt = (step.text || "").toString();
      const preview = txt.length > 160 ? txt.slice(0, 160) + "…" : txt;
      detail = `<div class="trace-detail">${escapeHTML(preview)}</div>`;
    }

    traceSection.innerHTML += `
      <div class="${cls}">
        <div class="trace-label">${escapeHTML(label)}</div>
        ${detail}
      </div>
    `;
  });
  if (elapsed_ms) {
    traceSection.innerHTML += `<div class="trace-detail" style="margin-top:8px;color:var(--nx-gray-500);">Total: ${(elapsed_ms/1000).toFixed(1)}s</div>`;
  }
}

function renderSources(sources) {
  if (!sources || sources.length === 0) {
    sourcesSection.style.display = "none";
    return;
  }
  sourcesSection.style.display = "block";
  sourceList.innerHTML = "";
  sources.forEach(s => {
    const kindClass = s.kind === "rag" ? "rag" : "";
    const tag = s.kind === "rag" ? "DOC" : s.kind === "genie" ? "MV" : "TL";
    sourceList.innerHTML += `
      <div class="source-item">
        <div class="source-icon ${kindClass}">${tag}</div>
        <div>
          <div class="source-name">${escapeHTML(s.label)}</div>
          <div class="source-meta">${s.kind === "genie" ? "Genie space" : s.kind === "rag" ? "Document knowledge" : "Tool"} ${s.id ? "· " + escapeHTML(s.id) : ""}</div>
        </div>
      </div>
    `;
  });
}

function updateConvoHeader(firstUserMessage) {
  if (firstUserMessage) {
    convoTitle.textContent = firstUserMessage.length > 80 ? firstUserMessage.slice(0, 80) + "…" : firstUserMessage;
    convoMeta.textContent = `Started just now · cross-source`;
  }
}

function pushRecent(question) {
  recentConversations.unshift({ q: question, ts: new Date() });
  if (recentConversations.length > 8) recentConversations.pop();
  renderRecent();
}

function renderRecent() {
  if (recentConversations.length === 0) {
    recentList.innerHTML = '<div class="recent-item empty">No conversations yet</div>';
    return;
  }
  recentList.innerHTML = recentConversations.map(r => `
    <div class="recent-item" title="${escapeHTML(r.q)}">
      ${escapeHTML(r.q)}
      <div class="recent-time">just now</div>
    </div>
  `).join("");
}

async function ask(message) {
  if (!message || !message.trim()) return;
  sendBtn.disabled = true;
  appendUserMessage(message);
  if (history.length === 0) {
    updateConvoHeader(message);
    pushRecent(message);
  }
  const thinkingEl = appendThinkingMessage();

  try {
    // 1) Kick off background job
    const startResp = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history }),
    });
    const startText = await startResp.text();
    let startData = null;
    try { startData = JSON.parse(startText); } catch (_) {}
    if (!startResp.ok || !startData?.job_id) {
      thinkingEl.remove();
      const isTimeout = /timeout|upstream/i.test(startText);
      const detail = startData?.detail || startText.slice(0, 400) || "Endpoint error";
      const hint = isTimeout ? "\n\nGateway timed out before the job could start." : "";
      appendAssistantMessage(`**Error (HTTP ${startResp.status}):** ${escapeHTML(detail)}${hint}`, [], null);
      sendBtn.disabled = false;
      return;
    }

    const jobId = startData.job_id;

    // Cache hit — render immediately from the first poll
    if (startData.status === "done" || startData.cached) {
      const pollResp = await fetch(`/api/chat/${jobId}`);
      const pollData = await pollResp.json();
      if (pollData?.result) {
        thinkingEl.remove();
        appendAssistantMessage(pollData.result.answer, pollData.result.sources, pollData.result.elapsed_ms, /*cached*/ true);
        renderTrace(pollData.result.trace, pollData.result.elapsed_ms);
        renderSources(pollData.result.sources);
        history.push({ role: "user", content: message });
        history.push({ role: "assistant", content: pollData.result.answer });
        sendBtn.disabled = false;
        return;
      }
    }

    // 2) Poll until done / error / timeout. Stream partial answer + trace as they arrive.
    const POLL_INTERVAL_MS = 1200;
    const MAX_WAIT_MS = 600_000; // 10 minutes
    const start = Date.now();
    let data = null;

    // Convert the thinking bubble into a live-streaming bubble.
    const streamEl = document.createElement("div");
    streamEl.className = "message assistant streaming-msg";
    streamEl.innerHTML = `
      <div class="msg-avatar assistant">NX</div>
      <div class="msg-content">
        <div class="routing-row" id="liveRouting"></div>
        <div class="md-body live-body" id="liveBody"><span class="typing"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span><span id="liveTimer">Routing…</span></span></div>
      </div>
    `;
    thinkingEl.replaceWith(streamEl);
    const liveBody = streamEl.querySelector("#liveBody");
    const liveRouting = streamEl.querySelector("#liveRouting");
    const liveTimer = streamEl.querySelector("#liveTimer");
    let lastTraceLen = 0, lastSourcesKey = "";

    while (true) {
      if (Date.now() - start > MAX_WAIT_MS) {
        throw new Error(`Supervisor did not complete within ${Math.round(MAX_WAIT_MS/60000)} minutes`);
      }
      await new Promise(r => setTimeout(r, POLL_INTERVAL_MS));
      const pollResp = await fetch(`/api/chat/${jobId}`);
      const pollText = await pollResp.text();
      let pollData = null;
      try { pollData = JSON.parse(pollText); } catch (_) {}

      if (!pollResp.ok) {
        streamEl.remove();
        appendAssistantMessage(`**Error polling job (HTTP ${pollResp.status}):** ${escapeHTML(pollData?.detail || pollText.slice(0,200))}`, [], null);
        sendBtn.disabled = false;
        return;
      }
      if (pollData?.status === "done") {
        data = pollData.result;
        break;
      }
      if (pollData?.status === "error") {
        streamEl.remove();
        appendAssistantMessage(`**Supervisor error:** ${escapeHTML(pollData.error || "unknown error")}`, [], null);
        sendBtn.disabled = false;
        return;
      }

      // Live updates
      const sec = pollData?.elapsed_seconds || 0;
      const partialAnswer = pollData?.partial_answer || "";
      const partialSources = pollData?.partial_sources || [];
      const partialTrace = pollData?.partial_trace || [];

      // Routing pills update
      const sourcesKey = partialSources.map(s => s.kind + ":" + s.label).join("|");
      if (sourcesKey !== lastSourcesKey) {
        lastSourcesKey = sourcesKey;
        liveRouting.innerHTML = partialSources.map(s => {
          const cls = s.kind === "rag" ? "rag" : s.kind === "genie" ? "genie" : "tool";
          const icon = s.kind === "rag" ? "📄" : s.kind === "genie" ? "⚡" : "🔧";
          return `<span class="routing-pill ${cls}">${icon} ${escapeHTML(s.label)}</span>`;
        }).join("");
      }

      // Streaming body — show partial answer if we have one, else show what we're doing
      if (partialAnswer) {
        liveBody.innerHTML = renderMarkdown(partialAnswer) + `<span class="cursor-blink">▌</span>`;
      } else {
        const lastStep = partialTrace[partialTrace.length - 1];
        const stage = lastStep
          ? (lastStep.step === "tool_call" ? `Calling ${lastStep.tool_label}…`
             : lastStep.step === "tool_result" ? `Got result from ${lastStep.tool_label}, thinking…`
             : lastStep.step === "handoff" ? `Active: ${lastStep.agent}`
             : "Routing…")
          : "Routing…";
        liveTimer.textContent = `${stage} ${sec}s`;
      }

      // Trace panel live update
      if (partialTrace.length !== lastTraceLen) {
        lastTraceLen = partialTrace.length;
        renderTrace(partialTrace, sec * 1000);
        renderSources(partialSources);
      }
    }

    streamEl.remove();
    appendAssistantMessage(data.answer, data.sources, data.elapsed_ms, data.cached);
    renderTrace(data.trace, data.elapsed_ms);
    renderSources(data.sources);

    history.push({ role: "user", content: message });
    history.push({ role: "assistant", content: data.answer });
  } catch (e) {
    thinkingEl.remove();
    appendAssistantMessage(`**Network error:** ${escapeHTML(e.message)}`, [], null);
  } finally {
    sendBtn.disabled = false;
    composerEl.focus();
  }
}

composerEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    const val = composerEl.value.trim();
    if (val) {
      composerEl.value = "";
      ask(val);
    }
  }
});

sendBtn.addEventListener("click", () => {
  const val = composerEl.value.trim();
  if (val) {
    composerEl.value = "";
    ask(val);
  }
});

// Auto-grow textarea
composerEl.addEventListener("input", () => {
  composerEl.style.height = "auto";
  composerEl.style.height = Math.min(composerEl.scrollHeight, 120) + "px";
});

// Quick prompts
document.addEventListener("click", (e) => {
  if (e.target.classList.contains("quick-prompt")) {
    const q = e.target.textContent.trim();
    composerEl.value = q;
    ask(q);
    composerEl.value = "";
  }
});

// New conversation
newChatBtn.addEventListener("click", () => {
  history = [];
  messagesEl.innerHTML = `
    <div class="empty-state">
      <div class="empty-icon">💭</div>
      <div class="empty-title">Ask about operations, finance, maintenance, or documents</div>
      <div class="empty-sub">The supervisor agent will decide which Genie space or document source to use, and show you the trace.</div>
      <div class="quick-prompts" style="margin-top:18px;padding:0;justify-content:center;">
        <span class="quick-prompt">Why are emergency vendor costs rising in NW-PowerPool?</span>
        <span class="quick-prompt">Top 5 outages by lost MWh this year</span>
        <span class="quick-prompt">What does RCA-2025-003 say about WIN-10130?</span>
        <span class="quick-prompt">Compare Apex vs CPS pricing</span>
      </div>
    </div>`;
  convoTitle.textContent = "New conversation";
  convoMeta.textContent = "Ask anything — the supervisor will route to the right source.";
  traceSection.innerHTML = '<h4>Supervisor Trace</h4><div class="inspector-empty">No trace yet — ask a question to see how the supervisor routes.</div>';
  sourcesSection.style.display = "none";
  composerEl.focus();
});

composerEl.focus();
