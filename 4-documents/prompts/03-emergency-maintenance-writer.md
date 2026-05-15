# Subagent Prompt — Emergency Maintenance Reports + Repair Approval Memos

Paste this entire prompt into a subagent. Adjust the absolute paths at the top to match where you've placed the repo on disk.

---

You are writing synthetic Emergency Maintenance Reports and Repair Approval Memos for a Databricks demo. The goal is a coherent multi-document narrative where an AI can later detect vendor cost arbitrage, replacement-vs-repair conflicts, and procedural shortcuts.

**MANDATORY READING FIRST:**
1. Read `<REPO>/4-documents/NARRATIVE_BIBLE.md` — every entity name, dollar value, and date must come from this bible.
2. Read `/tmp/narrative_bible.json` for specific outage IDs, asset tags, and dates.

**YOUR ASSIGNMENT — Write 10 markdown documents:**

## Emergency Maintenance Reports (6 files, EMR-2025-001 through EMR-2025-006)

Written by the vendor who performed the emergency work. These are the **vendor-side** narrative — they should sound like vendor field reports, often justifying their pricing.

Each EMR is 1-2 pages. Include:
- Header: Document ID, Vendor Letterhead (use the actual vendor name as the "From"), Date, Site, Asset, Outage ID, Cascadia Work Order ID, Cascadia Authorization (cite EPA-2024-11 where applicable)
- Section 1: Scope of Emergency Work
- Section 2: Findings (what the vendor saw)
- Section 3: Repairs Performed (parts, labor hours, materials)
- Section 4: Recommendations (this is where vendor bias shows — Apex pushes replacement, CPS pushes refurbishment)
- Section 5: Invoice Summary (labor + parts + travel + premium)
- Closing: Vendor signature, attached photos/manuals reference

**Specific EMRs:**

| EMR | Vendor | Anchor outage | Invoice approx | Vendor bias to show |
|---|---|---|---|---|
| EMR-2025-001 | Apex Emergency Grid Solutions | 2025-05-02 WIN-10058 NW-PowerPool-WIND-014 soc_drift, 227h | $412K | Recommends full inverter/battery management module replacement instead of capacitor swap. Justifies with "irreversible degradation." |
| EMR-2025-002 | Apex Emergency Grid Solutions | 2025-05-26 TRA-10561 NW-PowerPool-WIND-003 vibration_excess, 158h | $389K | Pushes full transformer windings replacement. CSM-7 oil-spectrometer step note: "performed annually per OEM guidance" (defending lighter cadence). |
| EMR-2025-003 | Apex Emergency Grid Solutions | 2025-08-28 WIN-10131 NW-PowerPool-WIND-024 overheating, 190h | $451K | Recommends Siemens Gamesa OEM-supervised gearbox replacement ($1.2M, separate quote). Cites OEM Manual Rev. 4.2 Section 8.3. |
| EMR-2025-004 | Cascadia Power Services Inc. (CPS) | 2025-10-07 WIN-10085 NW-PowerPool-WIND-003 overheating, 226h | $108K | Recommends cooling system overhaul ($185K, scheduled), NOT replacement. Cites Cascadia Standard MS-2025-03. **Make this the counter-example to Apex pattern.** |
| EMR-2025-005 | Apex Emergency Grid Solutions | 2025-11-12 SUB-10629 NW-PowerPool-WIND-024 soc_drift, 107h | $358K | Recommends Hitachi Energy OEM substation board swap. Notes "5th Apex deployment to WIND-024 in 12 months." |
| EMR-2025-006 | Apex Emergency Grid Solutions | 2025-12-10 TRA-10561 NW-PowerPool-WIND-003 overheating, 215h | $402K | **Repeat asset alert — same transformer treated in EMR-2025-002.** Recommends full replacement now. Cites prior emergency work as "evidence of imminent failure." |

## Repair Approval Memos (4 files, RAM-2025-001 through RAM-2025-004)

Written by Cascadia operations / procurement managers approving (or escalating) the emergency spend. Internal corporate tone, NOT vendor.

Each RAM is 1-1.5 pages. Include:
- Header: Document ID, Date, From (manager), To (CFO / Director of Operations), Subject, EPA reference if applicable
- Section 1: Background (cite the outage and EMR)
- Section 2: Vendor Recommendation
- Section 3: Cascadia Position (where it conflicts with vendor, say so)
- Section 4: Financial Justification (use bible numbers)
- Section 5: Approval Request / Decision

**Specific RAMs:**

| RAM | Approves / escalates |
|---|---|
| RAM-2025-001 | Approval of EMR-2025-001 invoice ($412K). Notes that this is the 4th Apex activation YTD and the cumulative is now over $1.4M. Approves with note to review Apex contract terms (cross-ref CAR-2025-004). |
| RAM-2025-002 | **Escalation** — declines the Siemens Gamesa gearbox replacement recommendation from EMR-2025-003 ($1.2M). Cites Cascadia Standard MS-2025-03 and MOC-2025-022 pending. Authorizes only the emergency stabilization work ($451K) and pushes the replacement decision to engineering. |
| RAM-2025-003 | **Approval** of EMR-2025-004 (CPS, $108K). Notes that this is in line with cooling system overhaul scope and represents 25% of the cost of equivalent Apex emergency work. Used as a benchmark for CAR-2025-004 (Apex performance review). |
| RAM-2025-004 | **Escalation** of EMR-2025-006 ($402K). Notes that this is the second emergency repair on TRA-10561 in 6 months (prior in EMR-2025-002). Asks engineering to convene a transformer replacement-vs-refurbish working group. Cites CAR-2025-002, MOC-2025-022, RCA-2025-002. |

## OUTPUT RULES

1. One markdown file per document: `<REPO>/4-documents/source-md/<DOC-ID>.md`
2. EMRs should sound like vendor field reports — use vendor's tone. CPS is professional/preventive; Apex is urgent/replacement-pushing.
3. RAMs are internal corporate. Often skeptical of vendor recommendations.
4. Cross-reference at least 2 other documents per file. Other agents in parallel are writing OIR-2025-001..010, CAR-2025-001..009, RCA-2025-001..005, VRA-2025-001..005, VTM files, OER files, FMS files. Reference them where natural.
5. Use ONLY entity names, vendor names, dollar values listed in the bible. Use EXACT asset tags and site names.
6. Avoid banned phrases ("delve into", "leverage", "robust", etc.).
7. Vendor invoice line items should be **realistic** — e.g., labor hours × rate, parts with part numbers, travel/per-diem, premium multipliers. Apex emergency rate is $420/hr with 1.5× weekend multiplier; CPS is $185/hr.

**WHEN DONE:** Return a summary (under 250 words) listing the 10 files plus the 3 most important cost contrasts you staged (e.g., Apex $412K vs CPS $108K for similar scope).
