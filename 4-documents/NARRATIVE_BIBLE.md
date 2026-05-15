# Narrative Bible — Renewable Energy Operations Documents

**Operator (fictional):** Cascadia Renewable Operations LLC
**Headquarters:** Portland, Oregon
**Fiscal Year:** 2025 (calendar year)
**Reporting unit:** All documents reference this operator. Use this name consistently.

This bible is the single source of truth for every synthetic document. Do NOT invent entity names, dates, dollar values, or asset tags that are not listed here or directly derived from the workspace data (queryable via /tmp/narrative_bible.json).

---

## 1. The Story Arc

Cascadia Renewable Operations ended FY2025 with headline revenue of **$857M** but is concealing a fast-deteriorating operational picture in its western footprint. Two clusters of forced outages — **Spring Vibration Cascade (May 2025)** and **Fall Overheating Sequence (October–November 2025)** — together caused 27,400 MWh of lost generation and triggered $14.4M in emergency vendor invoices. The same handful of assets keep failing. The same handful of vendors keep being called. Preventive maintenance plans have been "completed" on paper but the corrective action backlog tells a different story.

**The discovery the AI should make later:** The western region (NW-PowerPool) and CAISO are subsidizing operational neglect through emergency vendor contracts that financially reward outages rather than prevent them. Specifically:

- **Apex Emergency Grid Solutions** (the high-cost emergency contractor) bills 4× **Cascadia Power Services Inc.**'s rate for the same work and consistently recommends full component replacement instead of repair.
- **Siemens Gamesa**'s OEM service manual (Rev. 4.2) mandates blade-and-gearbox replacement at vibration thresholds 30% lower than what the revised internal Cascadia Standard MS-2025-03 requires. The OEM threshold drives unnecessary replacements; internal corrective actions to override it have been "pending engineering review" for 9 months.
- **GE**'s OEM manual specifies inspection intervals that predate the 2023 firmware refresh — operations teams have to choose between violating the manual or following the obsolete schedule.
- **NW-PowerPool-WIND-024** has 28+ forced outages across multiple assets but no asset-replacement plan; instead, Apex has been invoiced for emergency repairs 11 separate times on the same two turbines.

---

## 2. Entity Glossary (use EXACTLY these names)

### Regions (real data — use exactly)
| Code | Long name |
|---|---|
| NW-PowerPool | Northwest Power Pool (the "western region" — most problematic) |
| CAISO | California ISO |
| ERCOT | Electric Reliability Council of Texas |
| MISO | Midcontinent Independent System Operator |
| NYISO | New York Independent System Operator |
| PJM | PJM Interconnection |
| SPP | Southwest Power Pool |
| SE-Reliability | Southeast Reliability Coordinator |

### Headline problem sites (focus most narrative here)
| Site name | Region | Type | Capacity MW | Role in story |
|---|---|---|---|---|
| NW-PowerPool-WIND-024 | NW-PowerPool | wind | varies | Top problem site — 4 of top-10 worst outages |
| NW-PowerPool-WIND-014 | NW-PowerPool | wind | varies | Repeat failures on substation + GE turbine |
| NW-PowerPool-WIND-003 | NW-PowerPool | wind | varies | Late-year overheating cluster |
| CAISO-WIND-026 | CAISO | wind | varies | Highest single-asset lost MWh (WIN-10130) |
| SPP-WIND-025 | SPP | wind | varies | Nordex blade vibration issues |
| MISO-WIND-038 | MISO | wind | varies | Vestas anomaly — counter-example (well-managed) |

### Headline problem assets (use exact asset_tag and manufacturer)
| Asset tag | Type | Manufacturer | Site | Forced outages | Lost MWh |
|---|---|---|---|---|---|
| WIN-10130 | wind_turbine | Siemens Gamesa | CAISO-WIND-026 | 14 | 20,494 |
| WIN-10131 | wind_turbine | Siemens Gamesa | NW-PowerPool-WIND-024 | 8 | 17,239 |
| WIN-10054 | wind_turbine | Siemens Gamesa | CAISO-WIND-026 | 10 | 15,675 |
| WIN-10011 | wind_turbine | Siemens Gamesa | NW-PowerPool-WIND-024 | 12 | 14,411 |
| WIN-10007 | wind_turbine | Nordex | SPP-WIND-025 | 12 | 13,538 |
| SUB-10641 | substation_equipment | ABB | NW-PowerPool-WIND-014 | 15 | 13,362 |
| WIN-10016 | wind_turbine | GE | NW-PowerPool-WIND-014 | 16 | 12,589 |
| WIN-10058 | wind_turbine | GE | NW-PowerPool-WIND-014 | 12 | 11,606 |
| WIN-10106 | wind_turbine | Vestas | MISO-WIND-038 | 8 | 12,409 |
| WIN-10085 | wind_turbine | Vestas | NW-PowerPool-WIND-003 | 6 | 8,200 |
| TRA-10561 | transformer | Siemens | NW-PowerPool-WIND-003 | 8 | 7,900 |
| SUB-10629 | substation_equipment | Hitachi Energy | NW-PowerPool-WIND-024 | 4 | 9,800 |
| INV-10360 | inverter | Enphase | ERCOT-SOLAR-034 | 17 | varies |
| TRA-10570 | transformer | Siemens | NYISO-SOLAR-031 | 14 | varies |

### Vendors — 6 total (use exact names)

#### Equipment OEMs (provide manuals + warranty service)
| Vendor | Reputation in this narrative |
|---|---|
| **Vestas Wind Systems A/S** | Efficient, preventive-maintenance-focused. Their MISO-WIND-038 fleet shows lowest failure rate. Recommended baseline. |
| **Siemens Gamesa Renewable Energy** | OEM manual mandates expensive component replacement. Highest emergency cost per asset. Documentation conflict with revised internal standards. |
| **GE Renewable Energy** | OEM manual contains outdated procedures predating 2023 firmware refresh. Inspection intervals listed in manual no longer align with deployed firmware. |
| **Nordex SE** | Middle ground; reasonable manual but limited regional service presence. |
| **ABB Power Grids (Hitachi ABB Power Grids)** | Substation OEM. Repeat substation failures at NW-PowerPool-WIND-014. ABB manual recommends 4-year maintenance cycle; revised internal standard requires 2-year. |
| **Siemens Energy** | Transformer OEM. Manual conflicts with NW-PowerPool ambient temperature de-rating practice. |

#### Field service contractors (do the actual maintenance)
| Vendor | Role in story | Pricing pattern |
|---|---|---|
| **Cascadia Power Services Inc.** (CPS) | Preferred preventive partner. Bid-awarded 2023 multi-year MSA. Performs scheduled work in NW-PowerPool, MISO. | $185/hr labor; flat-rate parts mark-up 8%; emphasizes refurbishment over replacement. |
| **Apex Emergency Grid Solutions** (Apex) | The "expensive emergency vendor." Activated under Emergency Procurement Authorization (EPA) when CPS cannot mobilize within 4 hours. | $420/hr labor with 1.5× weekend multiplier; emergency parts mark-up 35%; consistently recommends replacement. |
| **Pinnacle Energy Maintenance** | Documentation-inconsistent vendor. Their service manuals reference deprecated procedures from a predecessor company they acquired in 2022. | $245/hr labor. Reasonable price but their documentation creates execution risk. |
| **Heartland Reliability Partners** | Newer entrant, attempting to standardize. Active mostly in CAISO, ERCOT. | $215/hr labor; offers performance-based contracts the company hasn't fully adopted yet. |

---

## 3. The Two Major Outage Periods

### Period A — "Spring Vibration Cascade" (May 2025)
- **NW-PowerPool stats:** 19 forced outages, 11,360 MWh lost generation
- **Adjacent month (June):** 21 outages, 13,226 MWh
- **Combined May-June lost MWh:** ~24,600 MWh
- **Story:** Q1 2025 budget freeze deferred 14 preventive maintenance work orders at NW-PowerPool-WIND-014 and -024. By May the bearings on WIN-10058, WIN-10016, and the SUB-10641 substation interconnect were running outside vibration spec. Apex Emergency was activated 6 times in the May–June window. Total Apex invoiced: **$4.6M**.
- **Key dates / outages to reference:**
  - 2025-05-02 — WIN-10058 (GE, NW-PowerPool-WIND-014) — soc_drift outage, 227h duration, 2,506.8 MWh lost
  - 2025-05-26 — TRA-10561 (Siemens, NW-PowerPool-WIND-003) — vibration_excess, 158h, 2,615.1 MWh lost
  - 2025-06-XX — Multiple smaller cascade events at WIND-014

### Period B — "Fall Overheating Sequence" (October-November 2025)
- **NW-PowerPool stats:** 27 forced outages combined, 22,996 MWh lost
- **Story:** Cooling-system maintenance neglect over summer caught up in October's first cold front. Siemens Gamesa was called for OEM warranty review on WIN-10131 — recommended full gearbox replacement at $1.2M per unit. Internal engineering challenged the recommendation; the case is still in dispute. Meanwhile, the same OEM service team won an emergency contract through Apex (Apex subcontracts to Siemens Gamesa OEM technicians at 1.8× rate).
- **Key dates / outages to reference:**
  - 2025-10-07 — WIN-10085 (Vestas, NW-PowerPool-WIND-003) — overheating, 226h, 3,740.6 MWh lost
  - 2025-11-12 — SUB-10629 (Hitachi Energy, NW-PowerPool-WIND-024) — soc_drift, 107h, 2,609.0 MWh
  - 2025-12-02 — WIN-10011 (Siemens Gamesa, NW-PowerPool-WIND-024) — efficiency_decline, 111h, 2,706.6 MWh
  - 2025-12-10 — TRA-10561 (Siemens, NW-PowerPool-WIND-003) — overheating, 215h, 3,558.6 MWh

---

## 4. Recurring procedural threads (use throughout)

These specific items should be referenced across multiple documents to create AI-detectable signals:

1. **Standard MS-2025-03** — Internal "Mechanical Standard, Revision 2025-03" (issued February 2025). Sets vibration thresholds and inspection intervals. Conflicts with Siemens Gamesa OEM Manual Rev. 4.2 and ABB Substation Manual SE-7100 §6.4.
2. **EPA-2024-11** — "Emergency Procurement Authorization" policy from November 2024. Allows bypass of competitive bid if mobilization needed in <4 hours. Apex has been activated under EPA 11 times in FY2025.
3. **CAR-2024-118** — "Preventive Maintenance Cadence Inadequate For Aging Wind Assets" — open corrective action from December 2024, still unimplemented as of Dec 2025.
4. **MOC-2025-022** — "Management of Change request" to override Siemens Gamesa OEM replacement threshold — submitted March 2025, still pending engineering review.
5. **Q1 budget freeze (Jan–Mar 2025)** — deferred 14 preventive WOs at NW-PowerPool; directly upstream of Period A.
6. **Cooling System Maintenance Procedure CSM-7** — applies to wind turbines; ambiguous between OEM manual and Cascadia operations procedure on whether oil-spectrometer testing is required quarterly (CPS does it) or annually (Apex does it).
7. **Fatigue Management Policy FMP-2** — limits overtime for technicians to 60 hr/wk. Repeatedly exceeded at NW-PowerPool during Period A; documented in CAR.

---

## 5. Dollar values that should be consistent across documents

| Item | Value (use exactly) |
|---|---|
| NW-PowerPool FY25 revenue | $121.1M |
| NW-PowerPool FY25 maintenance cost | $13.4M (under-reported per CAR) |
| NW-PowerPool FY25 net profit | $103.5M |
| FY25 NW-PowerPool emergency vendor invoices (Apex + Siemens Gamesa OEM service) | ~$8.9M (line-itemed) |
| Apex average emergency invoice | $385K |
| CPS equivalent scope estimate | $96K (1/4 of Apex) |
| Siemens Gamesa gearbox replacement quote (WIN-10131) | $1.2M per unit |
| Cooling system overhaul (internal estimate) | $185K per turbine |
| Period A total Apex invoiced | $4.6M |
| Period B total Apex invoiced | $3.7M |

---

## 6. Style and tone

- **Voice:** Corporate, operational, procedural. Write as if you're a maintenance engineer, plant manager, or compliance auditor, not a journalist.
- **Format:** Use document headers with consistent fields:
  - Document ID, Date, Author, Region, Site, Asset (if applicable)
  - Subject/Purpose/Distribution
  - Body: numbered sections with engineering content
  - Closing: signatures, references, distribution list
- **Banned phrases:** "delve into", "leverage", "in conclusion", "this analysis shows", "highlights the importance of", "robust", "synergize", "ensure that"
- **Required artifacts:** Reference real outage_ids (use realistic-looking IDs like OUT-2025-XXXX), work_order_ids (WO-2025-XXXXX), and dollar values from the bible.
- **Length:** 1.5 to 3 pages each. Engineering depth, not generic narration.
- **Cross-references:** Each document must reference at least 2 other documents by ID (creates the web of internal references AI can later follow).
- **Conflict signals:** Where two documents from different sources speak to the same issue, deliberately stage minor procedural conflicts (e.g., the OEM manual says X, the corrective action says do Y).

---

## 7. Document ID conventions

- Outage Investigation Report: `OIR-2025-NNN`
- Corrective Action Report: `CAR-2025-NNN`
- Emergency Maintenance Report: `EMR-2025-NNN`
- Vendor Repair Agreement: `VRA-2025-NNN`
- Vendor Technical Manual: `VTM-{vendor-code}-{rev}`
- Root Cause Analysis: `RCA-2025-NNN`
- Repair Approval Memo: `RAM-2025-NNN`
- Operational Escalation Report: `OER-2025-NNN`
- Field Maintenance Summary: `FMS-2025-NNN`

---

## 8. Required cross-document patterns

The AI should be able to discover, from reading the corpus:

1. **Vendor cost arbitrage:** Apex invoices for emergency scope ~4× CPS quotes for equivalent scheduled work.
2. **Replacement-vs-repair conflict:** Siemens Gamesa OEM (VTM) says replace; Cascadia Standard MS-2025-03 (CAR) says refurbish; MOC-2025-022 is the pending request to formalize the override.
3. **Manual obsolescence:** GE manual lists procedures invalidated by 2023 firmware refresh.
4. **Maintenance neglect → outage causation:** Q1 budget freeze (referenced in CARs) → 14 deferred preventive WOs → Period A outages.
5. **Repeat-failure pattern:** Same 3 NW-PowerPool sites generate disproportionate outages; same 5 assets account for 60%+ of NW-PowerPool's lost generation.
6. **Procedural shortcut under pressure:** During Period B, technicians bypassed CSM-7 oil-spectrometer step due to fatigue (documented in CAR-2025-XXX, RCA-2025-XXX).
7. **Documentation drift:** Pinnacle service docs reference pre-acquisition procedures; ABB manual cycle conflicts with Standard MS-2025-03.

End of bible.
