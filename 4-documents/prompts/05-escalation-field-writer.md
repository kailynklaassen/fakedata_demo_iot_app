# Subagent Prompt — Operational Escalation Reports + Field Maintenance Summaries

Paste this entire prompt into a subagent. Adjust the absolute paths at the top to match where you've placed the repo on disk.

---

You are writing synthetic Operational Escalation Reports and Field Maintenance Summaries for a Databricks demo. The goal is a coherent multi-document narrative where an AI can connect operational degradation patterns to executive-level concerns and field-level reality.

**MANDATORY READING FIRST:**
1. Read `<REPO>/4-documents/NARRATIVE_BIBLE.md` carefully.
2. Read `/tmp/narrative_bible.json` for additional anchors.

**YOUR ASSIGNMENT — Write 7 markdown documents:**

## Operational Escalation Reports (2 files, OER-2025-001 and OER-2025-002)

Senior leadership-level reports — escalating an operational pattern to the executive team. 2-3 pages each. Should feel like a VP of Operations writing to the COO/CFO.

Include:
- Header: Document ID, Date, From (VP-level title), To (COO/CFO/Board), Subject, Classification (Internal — Restricted Distribution)
- Executive Summary (2-3 paragraphs)
- Section 1: Pattern Description
- Section 2: Quantified Business Impact (dollars, MWh, hours — cite bible figures)
- Section 3: Root Causes (refer to CARs, RCAs)
- Section 4: Resources At Risk
- Section 5: Recommended Executive Action
- Section 6: Decision Required
- Closing: signature, references, distribution

**Specific OERs:**

| OER | Subject |
|---|---|
| OER-2025-001 | "Emergency Vendor Cost Escalation — Q3 FY2025" — Written ~September 2025 after Period A is fully accounted for. Highlights that Apex invoices YTD have reached $5.8M (line-item them), 4× the equivalent CPS scope estimate of $1.4M. Recommends immediate Apex contract renegotiation, accelerating Heartland Reliability Partners pilot (VRA-2025-004), and a formal review of EPA-2024-11. Notes that 11 of 11 emergency activations were at NW-PowerPool. Cite CAR-2025-001, CAR-2025-004, RCA-2025-001. |
| OER-2025-002 | "Western Region Operational Risk — Year-End FY2025 Assessment" — Written ~December 2025 after Period B. Lays out the full picture: 5 sites with recurring failures (NW-PowerPool-WIND-024, -014, -003 dominant), $8.9M emergency spend, deferred maintenance backlog of 31 work orders, and an unresolved OEM vs. internal-standard conflict (MOC-2025-022 pending 9 months). Recommends: capital plan for aging-asset replacement at WIND-024 site, formal OEM service contract renegotiation with Siemens Gamesa, and asset-level retirement decisions for WIN-10130 and TRA-10561. Cite OER-2025-001, RCA-2025-002, RCA-2025-003, RCA-2025-004, CAR-2025-002. |

## Field Maintenance Summaries (5 files, FMS-2025-001 through FMS-2025-005)

Weekly/monthly summaries from field maintenance leads — operational tempo at site level. 1-2 pages each. Tone: practical, ground-level, often noting frustration with policies or vendor delays.

Include:
- Header: Document ID, Reporting Period, Site/Region, Field Supervisor (invent realistic names — Latino, Asian, European surnames mixed), Distribution
- Section 1: Reporting Period Summary (planned vs. actual WOs)
- Section 2: Significant Events
- Section 3: Vendor Activity
- Section 4: Open Issues / Backlog
- Section 5: Resource & Safety Notes
- Section 6: Forward Look (next period)

**Specific FMSs:**

| FMS | Period & site |
|---|---|
| FMS-2025-001 | January 2025, NW-PowerPool, by field supervisor at WIND-024. Notes Q1 budget freeze impact — preventive work orders being deferred. Lists 14 deferred WO numbers. Notes WIN-10131 had its first overheating event Jan 14 (cite OIR-2025-005). Foreshadows trouble. |
| FMS-2025-002 | May 2025, NW-PowerPool, after the Spring Vibration Cascade begins. Notes Apex was called 3 times this month at average $400K per dispatch. Notes technician fatigue (links to CAR-2025-006). References WIN-10058 outage May 2 (OIR-2025-006), TRA-10561 May 26 (OIR-2025-007). |
| FMS-2025-003 | October 2025, NW-PowerPool, when WIN-10085 overheats Oct 7. Quotes CPS preventive recommendation in EMR-2025-004 vs. typical Apex pattern. Notes cooling system maintenance was deferred over summer due to wildfire access restrictions. |
| FMS-2025-004 | November 2025, all NW-PowerPool sites. Reports the SUB-10629 soc_drift event (OIR-2025-008), the 5th Apex deployment to WIND-024 in 12 months. Field supervisor explicitly notes: "We are now in an emergency-repair cycle that we cannot break out of without a maintenance plan reset." |
| FMS-2025-005 | December 2025, NW-PowerPool-WIND-003. Documents the TRA-10561 second emergency (OIR-2025-004) on the same transformer that already had an emergency in May. Captures field-level concern that "the same vendor is doing the same emergency repair on the same transformer." Recommend immediate engineering review. Cite RAM-2025-004 escalation. |

## OUTPUT RULES

1. One markdown file per document: `<REPO>/4-documents/source-md/<DOC-ID>.md`
2. OER tone: executive, polished but candid — written by someone who needs the C-suite to act.
3. FMS tone: practical, ground-level, occasionally frustrated. Field supervisors should sound like real people — references to weather, crew schedules, etc.
4. Cross-reference at least 2 other documents per file. Other subagents are writing OIR-2025-001..010, CAR-2025-001..009, EMR-2025-001..006, RAM-2025-001..004, RCA-2025-001..005, VRA-2025-001..005, VTM-* files in parallel.
5. Use ONLY entity names, vendor names, dollar values from the bible.
6. Avoid banned phrases ("delve into", "leverage", "robust", etc.).
7. OER-2025-002 should land like a board memo. FMS docs should feel like a field email or a daily-log entry typed up at end of week.

**WHEN DONE:** Return a summary (under 250 words) listing the 7 files and the most important executive recommendation made in OER-2025-002.
