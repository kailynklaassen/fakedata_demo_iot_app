# Utility Operations Intelligence — Databricks Demo

End-to-end Databricks demo for a renewable energy utility: structured operational data + 50 unstructured PDF documents, exposed through 3 Genie Spaces + 4 Metric Views, orchestrated by a multi-agent supervisor model, and surfaced through a branded FastAPI web app deployed as a Databricks App.

The demo tells a coherent story — *"emergency vendor costs are escalating in NW-PowerPool because the same problem-assets keep failing and Cascadia is stuck in an emergency-repair cycle with one expensive vendor"* — that can be discovered by an AI from any combination of structured queries and unstructured document retrieval.

## What's in this repo

```
.
├── 1-data/                 # Generate the 13 source tables (~11.5M rows)
│   ├── generate.py / .ipynb
│   └── sanity_sql.py / .ipynb
├── 2-metric-views/         # Build rollups + 4 metric views, validate all 55 measures
│   ├── build_metric_views.py / .ipynb
│   └── test_metric_views.py / .ipynb
├── 3-genie-spaces/         # Create 3 Genie Spaces via REST API
│   └── build_genie_spaces.py / .ipynb
├── 4-documents/            # Narrative bible, prompts, 50 source MD + 50 PDFs
│   ├── NARRATIVE_BIBLE.md
│   ├── anchor_narrative.py / .ipynb
│   ├── convert_and_upload.sh
│   ├── prompts/            # 5 reusable subagent prompts
│   ├── source-md/          # 50 source markdown files
│   └── pdfs/               # 50 generated PDFs (ready to upload)
├── 5-supervisor-model/     # UI walkthrough for building the supervisor agent
│   └── README.md
└── 6-app/                  # FastAPI / static UI Databricks App (NextEra-themed)
    ├── app.py              # backend: SSE streaming + in-app Q&A cache
    ├── app.yaml
    ├── deploy.sh           # one-command deploy
    ├── requirements.txt
    └── static/             # index.html, style.css, app.js, nextera_logo.png
```

Numbered prefixes are the **deployment order**.

Every step that has a `.py` script also has an equivalent `.ipynb` notebook — use whichever fits your workflow:
- **Notebook (.ipynb)** — open and run in a Databricks workspace or local Jupyter
- **Script (.py)** — run locally with `uv run --python 3.12 --with <deps> script.py`

## Fastest path — one-shot setup

Open **`setup_all.ipynb`** at the repo root in a Databricks workspace. Fill in the widgets at the top (catalog, schema, volume, warehouse ID, your email), then **Run All**. It runs every automatable step (1, 1b, 2, 2b, 3, 4) in order using `%run` against the child notebooks, so all of them share your widget values. Total runtime: ~25-35 minutes (dominated by the 10M-row telemetry generation).

Steps **5 (build the supervisor in Agent Bricks)** and **6 (deploy the Databricks App)** remain manual — they involve UI work or shell commands that don't make sense from inside a notebook. The README files in those folders walk you through them.

## Architecture

```
                                ┌──────────────────────────────────────┐
                                │  Databricks App (FastAPI + static UI) │
                                │   utility-ops-supervisor              │
                                └─────────────────┬────────────────────┘
                                                  │ POST /api/chat
                                                  ▼
                                ┌──────────────────────────────────────┐
                                │  Supervisor Model Serving Endpoint   │
                                │   mas-cf2369f5-endpoint              │
                                │   (Mosaic AI Agent Framework)        │
                                └─┬────────┬───────────────┬───────────┘
                                  │        │               │
            ┌─────────────────────┘        │               └─────────────────────┐
            ▼                              ▼                                     ▼
  ┌──────────────────┐         ┌──────────────────────┐              ┌────────────────────────┐
  │  3 Genie Spaces  │         │  4 UC Metric Views   │              │ Knowledge Assistant    │
  │  (chat UI tools) │ ◄────── │  grid_operations     │              │ over PDF volume:       │
  │                  │         │  financial_perf      │              │  /Volumes/.../reports  │
  │                  │         │  maintenance_work    │              │   (50 PDFs)            │
  │                  │         │  executive_summary   │              │                        │
  └────────┬─────────┘         └──────────┬───────────┘              └────────────┬───────────┘
           │                              │                                       │
           └──────────────────────────────┴───────────────────────────────────────┘
                                          │
                                          ▼
                              ┌────────────────────────────┐
                              │  Unity Catalog tables (13) │
                              │  + 2 daily rollups         │
                              │  + 50 PDFs in UC Volume    │
                              └────────────────────────────┘
```

## Prerequisites

1. A Databricks workspace with **Unity Catalog**, **Serverless SQL**, **Mosaic AI Agent Framework**, **Genie**, and **Databricks Apps** enabled.
2. A target catalog and schema you can write to.
3. Databricks CLI v0.296+ installed and authenticated.
4. Python 3.12 + [uv](https://github.com/astral-sh/uv) for running the scripts locally.
5. macOS users running the PDF generation step also need WeasyPrint system deps:
   ```bash
   brew install cairo pango gdk-pixbuf libffi glib
   ```

## End-to-end deployment (manual / per-step)

If you prefer to run each step individually (or you're running outside of Databricks):

```bash
# 1. Generate structured operational data
cd 1-data/ && uv run --python 3.12 --with polars --with numpy --with mimesis --with pandas --with 'databricks-connect>=16.4,<17.0' generate.py

# 2. Build rollup tables + 4 metric views
cd ../2-metric-views/ && uv run --python 3.12 --with 'databricks-connect>=16.4,<17.0' build_metric_views.py
uv run --python 3.12 --with 'databricks-connect>=16.4,<17.0' test_metric_views.py

# 3. Create 3 Genie spaces
cd ../3-genie-spaces/ && python3 build_genie_spaces.py
# (follow that folder's README to POST the create payloads via databricks CLI)

# 4. Upload the 50 PDFs to a UC Volume (already in 4-documents/pdfs/)
cd ../4-documents/ && bash convert_and_upload.sh
# (regenerating the PDFs from scratch is optional — see 4-documents/README.md)

# 5. Build the supervisor multi-agent system in the UI
# See 5-supervisor-model/README.md (manual UI steps in Mosaic AI Agent Framework)

# 6. Deploy the app
cd ../6-app/ && bash deploy.sh
```

## App-side features (step 6)

The Databricks App you deploy in step 6 includes:

- **Live streaming** — the supervisor's responses stream to the UI token-by-token as the multi-agent system generates them. Routing pills and the trace panel update as each tool call fires.
- **In-app Q&A cache** — LRU keyed on `(history + question)` hash, 1 hour TTL. Repeat questions return in <1 second with a `⚡ Cached` badge.
- **Async job pattern** — bypasses the Databricks Apps gateway 60s timeout; supports questions up to 10 minutes.
- **Trace inspector** — right-side panel shows the supervisor's reasoning chain: intent → tool routing → tool results → synthesis. Each tool call is color-coded (blue = Genie, green = document RAG).

## Total objects you'll end up with

| Tier | Count | Where |
| --- | --- | --- |
| Source tables | 13 | UC catalog/schema |
| Daily rollup tables | 2 | UC catalog/schema |
| Metric views | 4 | UC catalog/schema |
| Genie spaces | 3 | workspace-level |
| Unstructured docs (PDFs) | 50 | UC Volume `reports/` |
| Supervisor endpoint | 1 | model serving endpoints |
| Knowledge Assistant endpoint | 1 | model serving endpoints |
| Databricks App | 1 | workspace-level |

## Headline data points the AI can discover

- ERCOT had 433 forced outages, the most of any region
- NW-PowerPool generated $8.9M in emergency vendor invoices (4× equivalent CPS scope)
- WIN-10130 (Siemens Gamesa, CAISO-WIND-026) lost 20,494 MWh across 14 outages
- TRA-10561 was emergency-repaired twice by the same vendor 6 months apart
- Siemens Gamesa OEM manual mandates replacement at a vibration threshold lower than internal Standard MS-2025-03 — formal override (MOC-2025-022) pending engineering review for 9+ months

## Notes / known issues

- The narrative bible (`4-documents/NARRATIVE_BIBLE.md`) is the single source of truth for entity names, dates, and dollar values across all documents. Minor inter-document numeric drift exists on the Siemens Gamesa vibration threshold (3.5 vs 4.5 vs 6.0 mm/s across document groups) — direction of the narrative is consistent.
- All structured data is for calendar year 2025. If you need a different year, change `YEAR_START` / `YEAR_END` in `1-data/generate.py`.
- App uses the NextEra Energy color palette and logo. Replace `6-app/static/nextera_logo.png` and the CSS variables in `6-app/static/style.css` to rebrand.
