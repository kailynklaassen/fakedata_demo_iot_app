# Document Writer Prompts

These 5 prompts are designed to be pasted into 5 parallel subagents (e.g., Claude Code's `Agent` tool with `subagent_type: general-purpose`) to generate the 50 source markdown documents.

## How to use

1. Make sure `NARRATIVE_BIBLE.md` exists at the parent folder (`../NARRATIVE_BIBLE.md`).
2. Make sure `/tmp/narrative_bible.json` exists (run `anchor_narrative.py` in the parent folder).
3. Make sure the output directory exists: `mkdir -p ../source-md/`.
4. Spawn 5 parallel subagents — paste each prompt below into one. Each takes 5-10 minutes to run.
5. After all 5 finish, you should have **50 files** in `../source-md/`.
6. Run `../convert_and_upload.sh` to convert to PDF and upload to the UC Volume.

## Why 5 subagents and not 1?

- **Parallelism** — 5× faster wall-clock time
- **Topical consistency** — each subagent focuses on one document type's voice (vendor-side for EMRs, audit voice for CARs, executive tone for OERs, etc.)
- **Context efficiency** — each subagent only loads the part of the bible it needs

## Why not just one big prompt?

The 50-doc corpus needs to feel like it came from many different people in the organization (compliance team writes CARs, field supervisors write FMSs, vendors write EMRs on their letterhead). Splitting into 5 subagents naturally produces 5 distinct voices. A single agent tends to homogenize.

## Cross-document references

Each subagent is instructed to cite at least 2 other documents per file. Since the subagents run in parallel, they reference doc IDs they expect the *other* subagents to be creating (OIR-2025-001..010, CAR-2025-001..009, EMR-2025-001..006, etc.). The doc-ID conventions are listed in the bible.

## Document type → prompt mapping

| Prompt | Doc IDs |
| --- | --- |
| `01-outage-rca-writer.md` | OIR-2025-001..010, RCA-2025-001..005 |
| `02-corrective-actions-writer.md` | CAR-2025-001..009 |
| `03-emergency-maintenance-writer.md` | EMR-2025-001..006, RAM-2025-001..004 |
| `04-vendor-docs-writer.md` | VRA-2025-001..005, VTM-SIEMENS-GAMESA-4-2, VTM-GE-RENEWABLE-2023, VTM-ABB-SE7100, VTM-VESTAS-2025 |
| `05-escalation-field-writer.md` | OER-2025-001..002, FMS-2025-001..005 |
