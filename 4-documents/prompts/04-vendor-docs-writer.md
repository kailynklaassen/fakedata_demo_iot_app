# Subagent Prompt — Vendor Repair Agreements + Vendor Technical Manuals

Paste this entire prompt into a subagent. Adjust the absolute paths at the top to match where you've placed the repo on disk.

---

You are writing synthetic Vendor Repair Agreements and Vendor Technical Manuals for a Databricks demo. The goal is a coherent multi-document narrative where an AI can detect documentation conflicts (vendor manuals vs internal standards), pricing arbitrage, and replacement-vs-repair bias.

**MANDATORY READING FIRST:**
1. Read `<REPO>/4-documents/NARRATIVE_BIBLE.md` carefully.
2. Read `/tmp/narrative_bible.json` for additional anchors.

**YOUR ASSIGNMENT — Write 9 markdown documents:**

## Vendor Repair Agreements (5 files, VRA-2025-001 through VRA-2025-005)

Each VRA is the formal contract document between Cascadia Renewable Operations and a vendor. 2-3 pages each. Include:
- Header: Document ID, Effective Date, Term, Parties (Cascadia + Vendor), Governing Standard, Distribution
- Section 1: Scope of Services
- Section 2: Rate Schedule (hourly labor, parts mark-up, premium multipliers — use exact figures from bible)
- Section 3: Service Level Agreements (mobilization time, response time)
- Section 4: Approval & Authorization Workflow (cite EPA-2024-11 for emergency activations)
- Section 5: Performance Metrics (where applicable)
- Section 6: Limitations, Exclusions, Termination
- Closing: Authorized signatures, attachments

**Specific VRAs:**

| VRA | Vendor | Type | Key terms |
|---|---|---|---|
| VRA-2025-001 | Cascadia Power Services Inc. (CPS) | Preventive Multi-Year MSA | $185/hr labor; flat-rate parts mark-up 8%; performs scheduled work in NW-PowerPool, MISO. Strong preventive-maintenance focus. Includes performance bonus for outage-reduction targets. Effective Jan 2023, renewed through Dec 2027. |
| VRA-2025-002 | Apex Emergency Grid Solutions | Emergency Procurement Authorization | $420/hr labor; 1.5× weekend multiplier; emergency parts mark-up 35%; mobilization within 4 hours. NO performance metrics. NO outage-reduction targets. Effective under EPA-2024-11 since Nov 2024. **Already invoked 11 times in FY2025 — note this in the agreement preamble.** |
| VRA-2025-003 | Pinnacle Energy Maintenance | Regional Service Agreement | $245/hr labor; covers SPP, MISO supplementary scope. **Note:** their service documentation references procedures from "predecessor entity Pinnacle Industrial Services" acquired Q2 2022 — this is a known issue per CAR-2025-008. |
| VRA-2025-004 | Heartland Reliability Partners | Performance-Based Pilot | $215/hr labor with a 10% rebate based on outage-reduction outcomes. **Pilot program — not yet activated**; awaiting executive approval since Sept 2025. Cite the deferred decision as a quality signal. |
| VRA-2025-005 | Siemens Gamesa Renewable Energy (OEM Service) | OEM Warranty + Extended Service Contract | Covers WIN-10130, WIN-10131, WIN-10011, WIN-10054 (Siemens Gamesa wind turbines). Component replacement priced per OEM catalog — gearbox replacement $1.2M per unit. Mandates use of OEM Manual Rev. 4.2 procedures. Conflict with Cascadia Standard MS-2025-03 acknowledged in addendum (recently appended). |

## Vendor Technical Manuals (4 files, IDs as listed)

These are the OEM service / maintenance manuals — written in **vendor voice**, with all the formality and rigidity of an OEM document. 2-3 pages each. Include:
- Title page: Manual title, Revision number, Effective Date, Applicable Equipment Models
- Section 1: Equipment Overview
- Section 2: Maintenance Schedule (intervals, frequencies)
- Section 3: Inspection Procedures (with thresholds)
- Section 4: Replacement Criteria
- Section 5: Approved Parts & Materials
- Section 6: Warranty Conditions
- Note: include a few realistic-sounding step numbers, torque specs, part numbers, etc.

**Specific VTMs:**

| VTM file ID | Vendor / equipment | Key narrative |
|---|---|---|
| VTM-SIEMENS-GAMESA-4-2 | Siemens Gamesa Wind Turbine Service Manual, Rev. 4.2 (Jun 2024) | Vibration threshold for gearbox replacement: **3.5 mm/s RMS** (Cascadia internal Standard MS-2025-03 says **5.0 mm/s RMS**). Gearbox replacement is "recommended at 3.5 mm/s" with no refurbishment alternative documented. Applies to WIN-10130, WIN-10131, WIN-10011, WIN-10054. **This is the headline conflict.** |
| VTM-GE-RENEWABLE-2023 | GE Renewable Energy 1.5 MW Wind Turbine Operating Manual (effective 2023) | Inspection cadence references pre-2023 firmware. Cooling system inspection intervals stated as "every 18 months operational" — but the 2023 firmware refresh changed temperature reporting interval, making this cadence inconsistent. CAR-2025-007 has been raised for the conflict. Applies to WIN-10016, WIN-10058. |
| VTM-ABB-SE7100 | ABB Substation Manual SE-7100 §6.4 (Apr 2022, never updated) | Substation maintenance cycle: **48 months** (Cascadia Standard MS-2025-03 requires **24 months**). Applies to SUB-10641, SUB-10629 substation equipment. **Headline conflict #2.** |
| VTM-VESTAS-2025 | Vestas Wind Systems V-Series Maintenance Procedure, Rev. 2025-01 | The well-aligned manual — explicitly endorses preventive-first approach, integrates with Cascadia Standard MS-2025-03. **This is the counter-example to Siemens Gamesa.** Applies to WIN-10106, WIN-10085, and other Vestas-managed assets. |

## OUTPUT RULES

1. One markdown file per document: `<REPO>/4-documents/source-md/<DOC-ID>.md`
2. VRAs: Corporate/legal contract language — section headings, defined terms (e.g., "Mobilization Time", "Authorized Scope"), but readable. Reference EPA-2024-11 in VRA-2025-002. Include realistic dollar values.
3. VTMs: OEM voice — formal technical-manual style. Include explicit thresholds and specific procedures so other documents can cite them.
4. **The conflicts must be specific and quotable.** E.g., the Siemens Gamesa manual must literally say "3.5 mm/s RMS" so a CAR or RCA can later say "the OEM threshold of 3.5 mm/s conflicts with our Standard MS-2025-03's 5.0 mm/s."
5. Cross-reference at least 2 related documents per file (other VRAs/VTMs, CARs, EMRs, OIRs). Other subagents are writing OIR-2025-001..010, CAR-2025-001..009, EMR-2025-001..006, RAM-2025-001..004, RCA-2025-001..005, OER, FMS in parallel.
6. Use ONLY entity names, vendor names, dollar values from the bible.
7. Avoid banned phrases.

**WHEN DONE:** Return a summary (under 250 words) listing the 9 files plus the 3 most important documentation conflicts you staged (e.g., "Siemens Gamesa 3.5 mm/s vs Cascadia MS-2025-03 5.0 mm/s").
