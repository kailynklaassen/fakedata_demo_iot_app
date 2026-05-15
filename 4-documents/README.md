# 4 — Synthetic Operational Documents

50 PDFs that tell a coherent multi-document narrative around the structured data. Designed so an AI can later detect:
- vendor cost arbitrage (Apex 4× Cascadia Power Services for equivalent scope)
- replacement-vs-repair conflicts (OEM manual vs internal Standard MS-2025-03)
- maintenance-neglect → outage causation
- repeat-failure patterns (same vendor, same asset, same scope, no durable fix)

## What's in this folder

```
4-documents/
├── README.md                      (this file)
├── NARRATIVE_BIBLE.md             single source of truth for entity names, dates, $
├── anchor_narrative.py            queries the workspace to pull anchors into /tmp/narrative_bible.json
├── convert_and_upload.sh          MD → PDF → UC Volume
├── prompts/                       reusable subagent prompts (5 fan-out groups)
│   ├── README.md
│   ├── 01-outage-rca-writer.md
│   ├── 02-corrective-actions-writer.md
│   ├── 03-emergency-maintenance-writer.md
│   ├── 04-vendor-docs-writer.md
│   └── 05-escalation-field-writer.md
├── source-md/                     50 source markdown files
└── pdfs/                          50 generated PDFs (ready to upload)
```

## Document mix (50 total)

| Type | Count | Voice / role |
| --- | --- | --- |
| Outage Investigation Reports (OIR) | 10 | Reliability Engineer forensics |
| Root Cause Analyses (RCA) | 5 | Aggregated pattern-level analysis |
| Corrective Action Reports (CAR) | 9 | Compliance / audit findings |
| Emergency Maintenance Reports (EMR) | 6 | Vendor-side, on vendor letterhead |
| Repair Approval Memos (RAM) | 4 | Internal corporate, approves/escalates vendor spend |
| Vendor Repair Agreements (VRA) | 5 | Formal contracts |
| Vendor Technical Manuals (VTM) | 4 | OEM service manuals (with intentional conflicts) |
| Operational Escalation Reports (OER) | 2 | VP → COO / Board memos |
| Field Maintenance Summaries (FMS) | 5 | Field supervisor monthly reports |

## Just want the PDFs?

If you don't need to regenerate the documents, **the 50 PDFs in `pdfs/` are ready to upload as-is** to your UC Volume.

```bash
# 1. Create the volume (one-time)
databricks api post /api/2.1/unity-catalog/volumes --profile=<profile> --json '{
  "catalog_name":"<your-catalog>",
  "schema_name":"<your-schema>",
  "name":"reports",
  "volume_type":"MANAGED",
  "comment":"Synthetic operational PDFs"
}'

# 2. Upload all 50
for pdf in pdfs/*.pdf; do
  databricks fs cp --overwrite --profile=<profile> "$pdf" \
    "dbfs:/Volumes/<catalog>/<schema>/reports/$(basename $pdf)"
done
```

Or just run `bash convert_and_upload.sh` which does both convert (if any new .md exist) and upload (skips PDFs that are already there).

## Regenerate the documents

Useful if you want to change the narrative, add new asset patterns, or extend the corpus.

### Step A — Pull data anchors

The bible references specific outage IDs, dollar values, dates that come from the workspace data. Run either `anchor_narrative.ipynb` in the workspace or locally:

```bash
uv run --python 3.12 --with 'databricks-connect>=16.4,<17.0' anchor_narrative.py
```

Either produces `/tmp/narrative_bible.json` containing the concrete anchors the subagents use.

### Step B — Fan out 5 subagents in parallel

The 50 docs are split into 5 buckets, each handled by one subagent for parallelism + topical consistency. The prompts in `prompts/` are templates — paste each one to a separate subagent (e.g., in Claude Code, run 5 `Agent` calls in parallel).

Each subagent receives:
1. The `NARRATIVE_BIBLE.md` (mandatory reading — every entity name, date, $ value must come from it)
2. The anchor data in `/tmp/narrative_bible.json`
3. Its specific document assignment list (see each prompt file)

They write markdown files to `source-md/`.

| Prompt | Documents written |
| --- | --- |
| `01-outage-rca-writer.md` | 10 OIRs + 5 RCAs |
| `02-corrective-actions-writer.md` | 9 CARs |
| `03-emergency-maintenance-writer.md` | 6 EMRs + 4 RAMs |
| `04-vendor-docs-writer.md` | 5 VRAs + 4 VTMs |
| `05-escalation-field-writer.md` | 2 OERs + 5 FMSs |

### Step C — Convert + upload

```bash
bash convert_and_upload.sh
```

Converts each `source-md/<DOC-ID>.md` to `pdfs/<DOC-ID>.pdf` using the markdown-to-pdf converter (WeasyPrint), then `databricks fs cp`s each PDF to the UC Volume.

## Engineered semantic patterns (what the AI can later detect)

1. **Vendor cost arbitrage** — Apex Emergency Grid Solutions invoices ~4× Cascadia Power Services for equivalent scope (VRA-001 vs VRA-002 rate cards).
2. **Replacement-vs-repair conflict** — Siemens Gamesa OEM Manual Rev. 4.2 (VTM-SIEMENS-GAMESA-4-2) mandates replacement at a lower vibration threshold than Cascadia Standard MS-2025-03; the override (MOC-2025-022) has been pending 9 months.
3. **Manual obsolescence** — GE OEM manual (VTM-GE-RENEWABLE-2023) references procedures invalidated by 2023 firmware refresh; CAR-2025-007 documents the issue.
4. **Maintenance neglect → outage** — Q1 budget freeze in CAR-2025-001 deferred 14 PMs → Spring Vibration Cascade (RCA-2025-001).
5. **Repeat-failure pattern** — EMR-2025-002 and EMR-2025-006 are the same vendor performing emergency repair on the same transformer (TRA-10561) 6 months apart, both pushing replacement.
6. **Procedural shortcuts** — CSM-7 cooling-system step bypassed during peak demand (CAR-2025-006, RCA-2025-005).
7. **Escalation chain** — FMS-2025-004 (field) → OER-2025-001 (VP escalation Q3) → OER-2025-002 (Board memo year-end requesting $18M capital plan).

## Known caveat

Minor inter-document numerical drift on the Siemens Gamesa vibration threshold across document groups (3.5 vs 4.5 vs 6.0 mm/s). Narrative direction is consistent — OEM threshold is lower than internal, OEM mandates replacement, internal allows refurbishment. A retrieval system surfacing all 3 groups would flag this as a contradiction; depending on your demo goals that's either a feature ("see how AI catches inconsistency") or a thing to fix with a sed pass.
