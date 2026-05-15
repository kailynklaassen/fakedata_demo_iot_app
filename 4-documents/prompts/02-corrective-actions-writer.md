# Subagent Prompt — Corrective Action Reports

Paste this entire prompt into a subagent. Adjust the absolute paths at the top to match where you've placed the repo on disk.

---

You are writing synthetic Corrective Action Reports (CARs) for a Databricks demo. The goal is a coherent multi-document narrative where an AI can later "connect the dots" between vendor cost patterns, deferred maintenance, and recurring failures.

**MANDATORY READING FIRST:**
1. Read `<REPO>/4-documents/NARRATIVE_BIBLE.md` carefully — every entity name, dollar value, and date you use must come from this bible.
2. Read `/tmp/narrative_bible.json` for additional specific outage IDs, asset tags, and dates.

**YOUR ASSIGNMENT — Write 9 markdown documents (Corrective Action Reports):**

Each CAR is 1.5-3 pages, written from the perspective of a Reliability & Compliance team auditing operational practice. Each should:
- Identify a specific process or vendor failure
- Cite the evidence (outage IDs, work orders, dates)
- Recommend a specific corrective action
- Note who owns the action and a target completion date
- Stage at least one explicit **conflict with vendor guidance or OEM manual** where possible — this is critical for AI later-reasoning

## Header fields for each CAR

- Document ID, Issue Date, Author (Reliability & Compliance team — invent realistic names), CAR Status (Open / In-Progress / Pending Engineering Review)
- Subject, Affected Region/Site/Asset, Severity (Low/Medium/High/Critical), Owner, Target Close Date
- Distribution

## Body sections

1. Finding (the problem observed)
2. Evidence (specific outages, work orders, costs)
3. Root Cause Hypothesis
4. Conflict With Existing Guidance (if applicable — name the vendor manual, internal standard, or policy)
5. Recommended Corrective Action
6. Action Owner & Timeline
7. Implementation Status (most should be "Open" or "Pending"; only 1-2 "Completed")

## Specific CARs to write

| CAR | Subject |
|---|---|
| CAR-2025-001 | "Q1 2025 Budget Freeze Deferred 14 Preventive Maintenance Work Orders at NW-PowerPool" — direct upstream cause of Period A. Cite the deferred WO numbers (invent WO-2025-XXXXX style), the WIND-014 and WIND-024 affected assets, and the May–June outage cost. **Status: Open, repeatedly missed target dates.** |
| CAR-2025-002 | "Siemens Gamesa OEM Manual Rev. 4.2 Vibration Threshold Conflicts With Cascadia Standard MS-2025-03" — formal documentation of the disagreement. Note that MOC-2025-022 was submitted in March 2025 to override OEM threshold; still **pending engineering review**. Implicates WIN-10130, WIN-10131, WIN-10011. |
| CAR-2025-003 | "Cooling System Maintenance Procedure CSM-7 — Ambiguous Quarterly vs. Annual Oil-Spectrometer Frequency" — root of the Period B overheating cluster. CPS performs it quarterly, Apex annually. Different vendors interpret CSM-7 differently. |
| CAR-2025-004 | "Apex Emergency Contract Lacks Performance Criteria" — Apex has been activated 11 times in FY2025 under EPA-2024-11. Average invoice $385K. CPS equivalent scope quoted at $96K. Recommends performance-based renegotiation. |
| CAR-2025-005 | "ABB Substation Manual SE-7100 §6.4 Recommends 4-Year Cycle; Cascadia Standard MS-2025-03 Requires 2-Year" — conflict implicating SUB-10641 repeat failures (15 forced outages on a single substation interconnect). |
| CAR-2025-006 | "Fatigue Management Policy FMP-2 Repeatedly Exceeded During Period A" — technicians at NW-PowerPool logged 70-85 hr weeks during May–June 2025. Linked to procedural shortcuts in TRA-10561 servicing. |
| CAR-2025-007 | "GE Renewable Energy OEM Manual References Pre-2023 Firmware Inspection Cadence" — for WIN-10016, WIN-10058. Firmware refresh in 2023 invalidated manual procedures; updated manual never received. |
| CAR-2025-008 | "Pinnacle Energy Maintenance Service Documentation References Deprecated Pre-Acquisition Procedures" — found during audit of work performed at SPP-WIND-025. |
| CAR-2025-009 | "Repeat-Failure Assets Not Escalated To Engineering Review Per ER-3 Policy" — WIN-10131 had 8 forced outages before being flagged for engineering review; policy requires 3. Same pattern for WIN-10016 (16 outages), SUB-10641 (15 outages). |

## OUTPUT RULES

1. One markdown file per CAR: `<REPO>/4-documents/source-md/CAR-2025-NNN.md`
2. Cross-reference at least 2 other documents per CAR (other CARs, OIRs OIR-2025-001..010, EMRs EMR-2025-001..006, RCAs RCA-2025-001..005, or vendor manuals VTM-VESTAS-2025, VTM-SIEMENS-GAMESA-4.2, VTM-GE-2023, VTM-ABB-SE7100).
3. Use ONLY entity names, vendor names, dollar values listed in the bible.
4. **Avoid banned phrases** ("delve into", "leverage", "robust", etc.).
5. Engineering-realistic detail — cite specific thresholds, part numbers, regulatory standards (IEEE, IEC), and inspector names.
6. Tone: clinical, audit-style, factual. Documents should feel like they came out of a real compliance tool.

**WHEN DONE:** Return a summary (under 250 words) listing the 9 files plus 3 of the most important conflicts you staged.
