# Siemens Gamesa Wind Turbine Service Manual
## Revision 4.2 — June 2024

**Document Reference:** VTM-SIEMENS-GAMESA-4-2
**Manual Title:** Wind Turbine Service Manual — Geared Platform, 2.5 MW / 3.0 MW Class
**Revision:** 4.2
**Effective Date:** June 1, 2024
**Supersedes:** Revision 4.1 (October 2022)
**Issuer:** Siemens Gamesa Renewable Energy A/S, Service Engineering, Brande, Denmark
**Distribution Class:** Controlled — OEM service technicians, Authorized Service Providers, and Owner Engineering teams under active Extended Service Contract.

**Applicable Equipment Models (and Operator Asset Tags Under Active OEM Service):**
- SG 2.5-114 Geared platform — **WIN-10130** (CAISO-WIND-026), **WIN-10054** (CAISO-WIND-026)
- SG 3.0-132 Geared platform — **WIN-10131** (NW-PowerPool-WIND-024), **WIN-10011** (NW-PowerPool-WIND-024)

---

## Section 1 — Equipment Overview

1.1 The SG 2.5-114 and SG 3.0-132 are three-bladed, upwind, horizontal-axis wind turbines with a modular nacelle architecture and a step-up gearbox driving a doubly-fed induction generator. Both platforms share the **G4X gearbox family** (high-speed parallel-shaft stage on the generator side; two planetary stages upstream).

1.2 **Major Drivetrain Components.**
- Main shaft (forged, low-speed)
- Main bearings (front: spherical roller; rear: cylindrical roller)
- Main gearbox assembly — G4X family
- High-speed shaft and coupling
- Doubly-fed induction generator
- Yaw bearing and yaw drives (4× geared motors)
- Pitch system (electric, individual per blade)

1.3 **Critical Service Parameters.** Drivetrain vibration is the leading indicator of bearing and gear-stage degradation. Continuous condition monitoring is mandatory on all units under active OEM service per Section 3.

---

## Section 2 — Maintenance Schedule

2.1 **Mandatory Intervals.** OEM service personnel shall perform the following:

| Activity | Interval |
|---|---|
| Routine inspection (visual, lube level, fastener check) | Every **6 months** of operation |
| Full annual service (oil sample, vibration baseline, torque audit) | Every **12 months** of operation |
| Major-component inspection (gearbox endoscopy, bearing geometry) | Every **48 months** of operation |
| Gearbox oil change (full) | Every **36 months** or upon oil-condition trigger |
| High-speed bearing greasing | Every **6 months** |
| Yaw drive lubrication | Every **12 months** |

2.2 **Condition-Based Triggers.** The intervals above are minimums. Condition-based indicators (vibration, oil particle count, bearing temperature) shall override the calendar cadence where applicable. See Section 3 for vibration thresholds.

2.3 **OEM-Only Activities.** The following may only be performed by Siemens Gamesa-certified service personnel without forfeiture of Extended Service Contract coverage:
- Gearbox endoscopy procedures (Procedure SG-WTSM-04.2-§4.3);
- High-speed shaft alignment (Procedure SG-WTSM-04.2-§4.7);
- Pitch system controller firmware updates;
- Any disassembly of the main gearbox.

---

## Section 3 — Inspection Procedures

3.1 **Vibration Monitoring (Continuous).** All covered units are equipped with the Siemens Gamesa Condition Monitoring System (CMS-G4) providing continuous broadband RMS vibration measurement at the following measurement points:
- MP-1: Main bearing, axial
- MP-2: Main bearing, radial
- MP-3: Gearbox HSS bearing, radial
- MP-4: Gearbox planetary stage 1, radial
- MP-5: Generator drive-end bearing, radial

3.2 **Broadband RMS Vibration Thresholds (Gearbox — MP-3 and MP-4).**

| Level | Threshold (running mean, broadband) | Required Action |
|---|---|---|
| Normal | < 2.0 mm/s RMS | Continue normal operation |
| Elevated | 2.0 – 3.0 mm/s RMS | Schedule unscheduled inspection within 14 days |
| Alert | 3.0 – 3.5 mm/s RMS | Inspect within 7 days; review oil sample |
| **Replacement criterion** | **≥ 3.5 mm/s RMS** | **Gearbox replacement is recommended. No further operation above this threshold is supported by OEM.** |

3.3 **Procedure SG-WTSM-04.2-§3.4 (Gearbox Vibration Acceptance).** Step-by-step:

1. Confirm CMS-G4 measurement is valid (no sensor fault flag);
2. Verify reading is a 24-hour running mean, not a transient spike;
3. Cross-check against MP-3 and MP-4 simultaneously;
4. Pull a gearbox oil sample per Procedure SG-WTSM-04.2-§3.5 and submit to an OEM-approved laboratory;
5. If broadband RMS at MP-3 or MP-4 is at or above **3.5 mm/s RMS** for any 72-hour rolling window, proceed to Section 4.

3.4 **Oil Analysis Thresholds (selected).**
- ISO 4406 cleanliness code: ≤ 18/16/13 acceptable; > 19/17/14 triggers oil change.
- Fe content (ppm): ≤ 50 acceptable; > 100 triggers gearbox internal inspection.
- Cu content (ppm): ≤ 15 acceptable; > 30 triggers HSS bearing replacement evaluation.

3.5 **Bearing Temperature Thresholds.** Main bearing: 80°C alert; 95°C trip. HSS bearing: 85°C alert; 100°C trip.

---

## Section 4 — Replacement Criteria

4.1 **Gearbox Replacement — Mandatory OEM Recommendation.** Replacement of the main gearbox assembly is recommended by Siemens Gamesa where any of the following conditions are met:

(a) Broadband RMS vibration at MP-3 or MP-4 at or above **3.5 mm/s RMS** sustained over a 72-hour rolling window (see §3.2);

(b) Oil Fe content above 100 ppm with corroborating particle morphology indicating gear-tooth contact wear;

(c) Endoscopy revealing scoring, micropitting, or fatigue cracking on any gear tooth or bearing raceway beyond Class B per the Siemens Gamesa internal grading;

(d) Documented incident of catastrophic over-torque (e.g., emergency stop from full load above 1.5× rated).

4.2 **No Refurbishment Pathway.** Revision 4.2 does not document a refurbishment pathway for the G4X gearbox family. Refurbishment by third parties is not endorsed by Siemens Gamesa and is incompatible with continued Extended Service Contract coverage on the gearbox. The 4.2 procedure set provides only the **replacement** pathway. Operators electing to refurbish do so at their own risk and forfeit Extended Service Contract coverage of the replaced assembly.

4.3 **Generator Replacement.** Recommended on insulation-resistance failure (< 5 MΩ at rated test voltage), winding-resistance imbalance > 5%, or bearing temperature trips on consecutive thermal cycles.

4.4 **Main Bearing Replacement.** Recommended on vibration MP-1 or MP-2 above 4.5 mm/s RMS sustained, or visible spalling on inspection.

---

## Section 5 — Approved Parts & Materials

5.1 **Replacement Parts.** Only Siemens Gamesa OEM parts (part numbers SG-G4X-* for gearbox subassemblies, SG-GEN-* for generator subassemblies) are approved for use on covered units. Selected part numbers:

| Part Number | Description |
|---|---|
| SG-G4X-GB-3000-FL | Full gearbox assembly, 3.0 MW class |
| SG-G4X-GB-2500-FL | Full gearbox assembly, 2.5 MW class |
| SG-G4X-HSS-BRG-A1 | HSS bearing kit (matched pair) |
| SG-G4X-PL1-BRG-A1 | Planetary stage 1 bearing kit |
| SG-GEN-3000-DFIG-FL | Generator assembly, 3.0 MW DFIG |
| SG-YAW-DRV-M4-A2 | Yaw drive motor assembly |
| SG-PIT-CTL-V3 | Pitch system controller module v3 |

5.2 **Gearbox Lubricant.** Mobil SHC 632 or OEM-approved equivalent. **Do not** substitute non-approved synthetic gear oils.

5.3 **Fastener Torque (Selected).**
- Main shaft to gearbox input flange: **6,800 N·m ± 4%**, applied in a star pattern in three passes (40%, 70%, 100%).
- HSS coupling bolts: **920 N·m ± 4%**.
- Yaw bearing bolts: **2,400 N·m ± 5%**.

---

## Section 6 — Warranty Conditions

6.1 **OEM Warranty Coverage.** Initial 5-year OEM warranty covers manufacturing defects in materials and workmanship on the gearbox, generator, main bearings, pitch system, and yaw system, subject to compliance with this Manual.

6.2 **Extended Service Contract.** Continues coverage of the same components on the terms set out in the Extended Service Contract. Compliance with the maintenance cadence in Section 2 and the inspection thresholds in Section 3 is a condition of continued coverage.

6.3 **Forfeiture Conditions.** Extended Service Contract coverage on a given component is forfeit if:

(a) A non-OEM part is installed on that component;
(b) The component is refurbished by a non-Siemens-Gamesa-certified provider;
(c) Operation is continued above the **3.5 mm/s RMS** broadband vibration threshold (gearbox) for more than 72 hours without OEM authorization;
(d) Required OEM-only procedures (Section 2.3) are performed by non-certified personnel.

6.4 **OEM Position on Operator Override.** Where an Operator's internal standard prescribes a vibration threshold different from the **3.5 mm/s RMS** specified in this Manual, Siemens Gamesa's position is that the OEM threshold governs for the purpose of warranty determination. The Operator may, in its operational discretion, defer replacement; doing so does not bind Siemens Gamesa to continued coverage of the affected gearbox.

---

## Document Control

| Field | Value |
|---|---|
| Document Number | SG-WTSM-04.2 |
| Revision | 4.2 |
| Effective | June 1, 2024 |
| Approved By | Director, Service Engineering, Siemens Gamesa Renewable Energy A/S |
| Next Scheduled Revision Review | June 2027 |

**Note to Operator Engineering Teams.** Where this Manual is being applied under VRA-2025-005, the Operator-side procedural-conflict routing established in Addendum A of that Agreement (and MOC-2025-022) may flag specific OEM recommendations for Operator Engineering disposition prior to capital commitment. Such routing does not modify the OEM's recommendation contained in this Manual.
