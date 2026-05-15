# 5 — Supervisor Multi-Agent System (UI walkthrough)

This is the **only step that is not scripted**. The supervisor agent is built in the Databricks Mosaic AI **Agent Bricks** UI (the platform's no-code multi-agent builder). The output of this step is a model serving endpoint named something like `mas-<id>-endpoint` that the app (step 6) calls.

## What you're building

A multi-agent supervisor that orchestrates 3 Genie spaces + 1 Knowledge Assistant:

```
User question
    ↓
┌─────────────────────────────────────┐
│  Supervisor (Claude Haiku 4.5)      │  ← the orchestrator
│  Decides which tool(s) to call      │
└──────┬───────┬───────┬──────────────┘
       ↓       ↓       ↓        ↓
   Genie:   Genie:  Genie:   Knowledge
   Grid Ops Finance Maint    Assistant
                             (50 PDFs)
```

## Prerequisites

- Steps 1-4 complete (Unity Catalog data, metric views, Genie spaces, PDFs in a UC Volume)
- Your workspace has Agent Bricks enabled

## Step A — Build the Knowledge Assistant (RAG over PDFs)

1. Databricks workspace → left nav **AI/ML → Agents** → **Create** → **Knowledge Assistant**
2. Configure:
   - **Name:** `Utility Operations Knowledge Assistant`
   - **Knowledge Source:** Unity Catalog Volume → select `<catalog>.<schema>.reports`
   - **Embedding model:** default (BGE small or similar)
   - **Answer model:** **Claude Haiku 4.5** (faster) — important for latency
   - **Retrieval (`top_k`):** 5-8 (don't leave at default 20; you only have 50 docs)
   - **Reranker:** off (the corpus is small enough that reranking adds latency without quality gain)
3. Save and deploy. Note the resulting endpoint name (e.g. `ka-<id>-endpoint`) — you'll need it in Step B.
4. Test in the playground — ask "What does RCA-2025-001 say?" and confirm it returns text with citations.

## Step B — Build the Multi-Agent System

1. Databricks workspace → **AI/ML → Agents** → **Create** → **Multi-Agent System**
2. **Name:** `Utility Operations Supervisor`
3. **Supervisor model:** **Claude Haiku 4.5** (Databricks Foundation Model APIs)
4. **System prompt** (paste this — tuned for speed and clean routing):

   ```
   You are an operations intelligence assistant for a renewable energy utility.

   You orchestrate four expert tools. Route to the right one(s) and synthesize a clear, concise answer.

   Tool selection rules:
   - Numeric / operational metrics (outages, capacity factor, MTBF/MTTR) → call Grid Operations Genie.
   - Revenue, OpEx, profit margin, market exposure → call Financial Performance Genie.
   - Work orders, technicians, preventive vs reactive, safety → call Maintenance & Workforce Genie.
   - Anything about specific reports (OIR, CAR, EMR, VRA, VTM, OER, FMS) or root-cause narratives → call the Knowledge Assistant.

   When a question needs both structured numbers AND document context, call the relevant Genie space AND the Knowledge Assistant in parallel. Do not wait for one before calling the next.

   Answer style:
   - Lead with the direct answer in 1-2 sentences.
   - Then back it with bullet points or a small table.
   - Cite document IDs inline (e.g. "see RCA-2025-001").
   - Never speculate. If a tool returns no data, say so.
   ```

5. **Add tools** (4 total):

   | Tool name (display) | Type | Target |
   | --- | --- | --- |
   | Grid Operations | Genie Space | space ID from step 3 (Grid Ops) |
   | Financial Performance | Genie Space | space ID from step 3 (Financial) |
   | Maintenance & Workforce | Genie Space | space ID from step 3 (Maintenance) |
   | Utility Operations Knowledge | Endpoint | the `ka-*-endpoint` from Step A |

6. **Performance settings:**
   - **Allow parallel tool calls:** ✅ ON (critical — cuts multi-source latency 30-40%)
   - **Max iterations:** 6
   - **Prompt caching:** ✅ ON if available (cuts repeat-turn latency)
   - **Streaming:** ✅ ON (the app uses this for live response rendering)

7. **Save and Deploy.** Agent Bricks creates a serving endpoint `mas-<id>-endpoint`. Note that ID — you'll set it in `6-app/app.yaml`.

## Step C — Grant the App's Service Principal Access (after step 6 creates the app)

Once you've created the Databricks App in step 6, give its service principal `CAN_QUERY` on the supervisor endpoint:

```bash
# Replace SP_ID with the app's service_principal_client_id from `databricks apps get <app>`
SP_ID=<service-principal-client-id>
ENDPOINT_ID=$(databricks serving-endpoints get mas-<id>-endpoint --profile=<profile> --output=json | jq -r .id)
cat > /tmp/grant.json << EOF
{"access_control_list":[{"service_principal_name":"$SP_ID","permission_level":"CAN_QUERY"}]}
EOF
databricks api patch "/api/2.0/permissions/serving-endpoints/$ENDPOINT_ID" --profile=<profile> --json @/tmp/grant.json
```

Also grant the SP `CAN_QUERY` on the Knowledge Assistant endpoint, `CAN_RUN` on each Genie space, `CAN_USE` on the warehouse, and `USE_CATALOG`/`USE_SCHEMA`/`SELECT`/`READ_VOLUME`/`EXECUTE` on the catalog + schema. See `6-app/README.md` for the full grant script.

## How to verify the supervisor works

Once deployed, test directly:

```bash
cat > /tmp/test.json << 'EOF'
{"input": [{"role":"user","content":"Top 3 regions by forced outage count this year?"}]}
EOF
databricks api post /serving-endpoints/mas-<id>-endpoint/invocations --profile=<profile> --json @/tmp/test.json
```

Expected: ~15-25s response with structured output items showing tool calls (look for `function_call` items with `name: "genie-<space_id>"` or `name: "ka-..."`).

## Performance tuning checklist (do these for fastest demos)

| Setting | Why | Where |
| --- | --- | --- |
| Supervisor model = Haiku 4.5 (not Sonnet) | 2-5× faster LLM thinking | Multi-Agent System edit screen |
| KA answer model = Haiku 4.5 | Faster doc Q&A | Knowledge Assistant edit screen |
| KA top_k = 5-8 | Less vector search work | Knowledge Assistant edit screen |
| KA reranker = off | Saves a model call | Knowledge Assistant edit screen |
| Parallel tool calls = ON | Cuts cross-source latency 30-40% | Multi-Agent System advanced settings |
| Streaming = ON | Lets the app render incrementally | Multi-Agent System advanced settings |
| Endpoint scale-to-zero = OFF (or min_replicas = 1) | Avoids 30-60s cold start | Endpoint edit |
| SQL warehouse size = Medium or Large + auto-stop ≥ 30 min | Faster Genie SQL exec | SQL Warehouse settings |
| Prompt caching = ON | Cheaper + faster repeated turns | Multi-Agent System advanced (if available in your version) |

## How the app talks to this supervisor

`6-app/app.py` reads `SUPERVISOR_ENDPOINT` from `6-app/app.yaml`, then streams Server-Sent Events from `POST /serving-endpoints/<endpoint>/invocations` with `{"input": [...], "stream": true}`. The app parses these events into a UI-friendly trace and surfaces partial answers / partial routing pills to the user as they arrive.

If you want to swap the supervisor (e.g., to a new version of the MAS endpoint), the only change required is updating `SUPERVISOR_ENDPOINT` in `6-app/app.yaml` and re-deploying.
