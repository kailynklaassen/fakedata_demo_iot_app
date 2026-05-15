# Subagent Prompt — Outage Investigation Reports + Root Cause Analyses

Paste this entire prompt into a subagent. Adjust the absolute paths at the top to match where you've placed the repo on disk.

---

You are writing synthetic operational documents for a Databricks demo. The goal is a coherent multi-document narrative where an AI can later "connect the dots" between vendor cost patterns, deferred maintenance, and recurring failures.

**MANDATORY READING FIRST:**
1. Read `<REPO>/4-documents/NARRATIVE_BIBLE.md` carefully — every entity name, dollar value, and date you use must come from this bible (or be a direct, plausible extrapolation).
2. Read `/tmp/narrative_bible.json` for additional specific outage IDs, asset tags, dates, and lost MWh figures from the actual workspace data.

**YOUR ASSIGNMENT — Write 15 markdown documents:**

## Outage Investigation Reports (10 files, IDs OIR-2025-001 through OIR-2025-010)

Each should be a forensic investigation of a specific outage or cluster. Aim for 1.5-3 pages each. Include:
- Header: Document ID, Report Date, Author (use realistic engineer names like "Marcus Chen, Sr. Reliability Engineer"), Region, Site, Asset, Outage ID(s), Distribution
- Section 1: Outage Summary (date, duration in hours, lost MWh)
- Section 2: Timeline of Events (with timestamps)
- Section 3: Telemetry Observations (overheating / vibration / efficiency / SoC numbers — make them plausible)
- Section 4: Restoration Activities (which vendor, scope, cost where known)
- Section 5: Preliminary Root Cause
- Section 6: Recommendations (cross-reference related CARs, RCAs)
- Closing: signatures + distribution list

**Specific outages to cover (use these as the anchors — one per OIR):**

| OIR | Outage anchor |
|---|---|
| OIR-2025-001 | 2025-04-11, SUB-10629, NW-PowerPool-WIND-024, soc_drift, 195h, 4,754.8 MWh lost |
| OIR-2025-002 | 2025-08-28, WIN-10131, NW-PowerPool-WIND-024, overheating, 190h, 4,632.9 MWh lost |
| OIR-2025-003 | 2025-10-07, WIN-10085, NW-PowerPool-WIND-003, overheating, 226h, 3,740.6 MWh lost |
| OIR-2025-004 | 2025-12-10, TRA-10561, NW-PowerPool-WIND-003, overheating, 215h, 3,558.6 MWh lost |
| OIR-2025-005 | 2025-01-14, WIN-10131, NW-PowerPool-WIND-024, overheating, 139h, 3,389.3 MWh — first event of the year, foreshadows pattern |
| OIR-2025-006 | 2025-05-02, WIN-10058, NW-PowerPool-WIND-014, soc_drift, 227h, 2,506.8 MWh lost — opening event of Spring Vibration Cascade |
| OIR-2025-007 | 2025-05-26, TRA-10561, NW-PowerPool-WIND-003, vibration_excess, 158h, 2,615.1 MWh lost — Period A continuation |
| OIR-2025-008 | 2025-11-12, SUB-10629, NW-PowerPool-WIND-024, soc_drift, 107h, 2,609.0 MWh — Period B mid-event |
| OIR-2025-009 | 2025-12-02, WIN-10011, NW-PowerPool-WIND-024, efficiency_decline, 111h, 2,706.6 MWh |
| OIR-2025-010 | CAISO-WIND-026 multi-event roll-up on WIN-10130 (Siemens Gamesa) — highest single-asset lost generation of the year (~20,494 MWh across 14 outages) |

## Root Cause Analysis Documents (5 files, IDs RCA-2025-001 through RCA-2025-005)

Each RCA aggregates multiple outage events into a deeper analysis. Aim for 2-3 pages each. Include:
- Header with executive summary
- Failure Mode classification
- Fishbone / contributing factors
- Timeline of relevant CARs and outages
- Quantified business impact (cite specific dollar values from bible)
- Long-term corrective recommendations
- Vendor performance commentary where relevant

**Specific RCAs to write:**

| RCA | Theme |
|---|---|
| RCA-2025-001 | Spring Vibration Cascade — the May–June 2025 outage cluster at NW-PowerPool-WIND-014/-024. Trace back to Q1 budget freeze, deferred preventive WOs, technicians exceeding FMP-2 fatigue thresholds. Reference Period A dollar figure ($4.6M Apex). |
| RCA-2025-002 | Fall Overheating Sequence — Oct–Dec 2025 outages at NW-PowerPool-WIND-003 and -024. Cooling system maintenance neglect over summer. Cite specific outages from OIR-2025-003, -004, -008, -009. |
| RCA-2025-003 | WIN-10130 chronic failure pattern (CAISO-WIND-026) — 14 outages, 20,494 MWh lost. Siemens Gamesa OEM replacement recommendation conflict with Cascadia Standard MS-2025-03. Reference MOC-2025-022 pending. |
| RCA-2025-004 | NW-PowerPool-WIND-014 substation cascading failures (SUB-10641 + WIN-10016 + WIN-10058). 43 combined forced outages. Address ABB documentation conflict. |
| RCA-2025-005 | Procedural shortcut analysis — bypassing CSM-7 oil-spectrometer step during peak demand. Implicated in TRA-10561 and WIN-10131 overheating events. |

## OUTPUT RULES

1. **One markdown file per document**, written to `<REPO>/4-documents/source-md/<DOC-ID>.md`.
2. Each document must reference **at least 2 other documents by ID** (e.g., "See related CAR-2025-003" or "Following on RCA-2025-001 we…"). Cross-reference across the corpus — invent CAR/EMR/RAM IDs reasonably; other subagents are writing the actual CARs (CAR-2025-001..009), EMRs (EMR-2025-001..006), RAMs (RAM-2025-001..004), VRAs/VTMs/OERs/FMSs in parallel.
3. Use ONLY entity names, vendor names, dollar values listed in the bible. Use **exact** asset tags (WIN-10131, SUB-10641, etc.) and site names (NW-PowerPool-WIND-024, etc.).
4. **Avoid banned phrases** listed in the bible ("delve into", "leverage", "robust", "synergize", etc.).
5. Make documents feel **engineering-realistic** — include specific telemetry numbers, work order IDs (use format WO-2025-NNNNN), part numbers when relevant, weather conditions, technician names from a small consistent pool you invent and reuse.
6. Stage conflicts deliberately: where an OIR cites Siemens Gamesa OEM Manual Rev. 4.2, ensure a corresponding RCA references that this conflicts with Cascadia Standard MS-2025-03 and MOC-2025-022.

**WHEN DONE:** Return a summary listing the 15 files you created, plus 3-5 of the cross-document references you wove in. Under 300 words.
