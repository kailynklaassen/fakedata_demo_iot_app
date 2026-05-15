# Vestas Wind Systems V-Series Maintenance Procedure
## Revision 2025-01

**Document Reference:** VTM-VESTAS-2025
**Manual Title:** V-Series Wind Turbine Maintenance Procedure — V100 / V112 / V117 Platforms
**Revision:** 2025-01
**Effective Date:** January 20, 2025
**Supersedes:** Revision 2023-04 (October 2023)
**Issuer:** Vestas Wind Systems A/S, Service Engineering, Aarhus, Denmark
**Distribution Class:** Controlled — Authorized Service Providers, Owner Engineering teams.

**Applicable Equipment Models (and Operator Asset Tags):**
- Vestas V112-3.45 MW — **WIN-10106** (MISO-WIND-038)
- Vestas V117-3.45 MW — **WIN-10085** (NW-PowerPool-WIND-003)
- Additional Vestas V100 and V112 platforms across Operator's fleet under standard OEM service.

---

## Preface — Preventive-First Approach

Vestas Wind Systems' service engineering philosophy, as expressed in this revised Manual, gives explicit priority to:

(a) **Continuous condition monitoring** as the leading indicator of component health, rather than fixed calendar intervals alone;
(b) **Refurbishment in place** of degraded gearboxes, bearings, and pitch components where the failure mode is consistent with documented refurbishment criteria in Section 4 below;
(c) **Replacement only at clearly documented end-of-life criteria** that integrate vibration, oil-analysis, and bearing-temperature evidence rather than any single threshold.

Revision 2025-01 of this Manual is **expressly written to integrate with operator-side internal standards** where those standards exist. Operators with documented internal standards (such as Cascadia Renewable Operations' Standard MS-2025-03) are encouraged to follow the operator-side cadence and threshold provisions where these are at least as conservative as this Manual's content. Where this Manual is more conservative, this Manual governs; where the operator standard is more conservative, the operator standard governs. The Manual is not in conflict with Standard MS-2025-03 and was reviewed against MS-2025-03 §4 (vibration) and §6 (cooling) prior to release.

This explicitly integrated approach distinguishes this Manual from the procedural posture of some peer-OEM service manuals; see, for contrast, VTM-SIEMENS-GAMESA-4-2 Section 6.4 and CAR-2025-005 / CAR-2025-007 in Operator's corrective-action system.

---

## Section 1 — Equipment Overview

1.1 The V-Series turbines covered by this Manual are three-bladed, upwind, horizontal-axis units in the 3.0 – 3.5 MW class. The drivetrain is a medium-speed configuration with a two-stage planetary gearbox and a permanent-magnet generator on the V117 platform; the V112 uses a doubly-fed induction generator.

1.2 **Major Components.**
- Main shaft and main bearing (spherical roller)
- Two-stage planetary gearbox — Vestas VG2 family
- Generator (PMG on V117; DFIG on V112)
- Cooling subsystem (oil cooler, generator coolant, converter coolant)
- Yaw drives (6× on V117)
- Pitch system (electric, individual per blade)

1.3 **Controller.** Vestas VMP-Global controller, firmware 4.2 or later. Telemetry sampling rate of 1 sample per minute on temperature and vibration channels.

---

## Section 2 — Maintenance Schedule

2.1 **Cadence (Calendar-Based Minimums, Subject to Condition-Based Override).**

| Activity | Interval |
|---|---|
| Routine inspection | Every 6 months operational |
| Annual service (oil sample, vibration baseline, torque audit) | Every 12 months operational |
| Major-component inspection (gearbox endoscopy, bearing geometry) | Every 36 months operational |
| Gearbox oil change | Every 36 months or upon oil-condition trigger |
| Cooling system inspection (full) | **Every 12 months operational** — aligned with Operator CSM-7 quarterly oil-spectrometer step where applicable |
| Yaw drive lubrication | Every 12 months operational |
| Pitch system inspection | Every 12 months operational |

2.2 **Condition-Based Override.** Where continuous condition monitoring indicates accelerated degradation, the calendar cadence above is to be shortened. Vestas Service Engineering will support operator-side decisions to shorten intervals without prejudice to warranty.

2.3 **Operator Alignment.** Operators using Cascadia Standard MS-2025-03 may rely on MS-2025-03 §3 cadence; Vestas confirms that MS-2025-03 §3 intervals fall within the bounds of this Manual.

---

## Section 3 — Inspection Procedures

3.1 **Vibration Monitoring (Procedure VS-VTM-2025-§3.2).** Broadband RMS at gearbox HSS bearing and planetary stage 1.

| Level | Threshold (running mean, broadband) | Required Action |
|---|---|---|
| Normal | < 3.0 mm/s RMS | Continue normal operation |
| Elevated | 3.0 – 5.0 mm/s RMS | Inspect at next scheduled outage; pull oil sample |
| Alert (refurbishment evaluation) | 5.0 – 7.0 mm/s RMS | Schedule refurbishment evaluation per Section 4.1 |
| Replacement evaluation | ≥ 7.0 mm/s RMS or with corroborating metallurgical evidence | Section 4.2 |

This three-tier structure (normal → refurbishment → replacement) is intentionally aligned with Cascadia Standard MS-2025-03 §5.4.

3.2 **Oil Analysis Thresholds.**
- ISO 4406 cleanliness code: ≤ 19/17/14 acceptable; > 20/18/15 triggers oil change.
- Fe content (ppm): ≤ 70 acceptable; > 120 triggers gearbox internal inspection.
- Cu content (ppm): ≤ 20 acceptable; > 35 triggers HSS bearing evaluation.

3.3 **Bearing Temperature Thresholds.** Main bearing: 82°C alert; 95°C trip. HSS bearing: 87°C alert; 100°C trip.

3.4 **Cooling System Inspection.** Per Operator CSM-7 procedure as integrated with this Manual; quarterly oil-spectrometer step is endorsed.

---

## Section 4 — Replacement Criteria

4.1 **Refurbishment Pathway (the Preferred First Action).** Where broadband vibration is in the 5.0 – 7.0 mm/s RMS band, Vestas authorizes and documents the following refurbishment activities, performed by Vestas-certified service partners (which include Cascadia Power Services Inc. under VRA-2025-001 as a Vestas-certified service provider in NW-PowerPool and MISO):

(a) HSS bearing replacement in place;
(b) Planetary stage 1 bearing replacement in place;
(c) Gear-tooth re-profiling or selective tooth replacement on documented Class B wear;
(d) Coupling alignment and rebalancing.

Refurbishment is the **preferred first action** and is fully supported by Extended Service Contract coverage, where applicable.

4.2 **Replacement Pathway (Only Above 7.0 mm/s RMS or with Corroborating Evidence).** Full gearbox replacement is indicated where:

(a) Broadband vibration at HSS or planetary stage 1 ≥ 7.0 mm/s RMS sustained, OR
(b) Vibration ≥ 5.0 mm/s RMS *and* oil Fe content > 150 ppm with corroborating particle morphology, OR
(c) Endoscopy reveals scoring or fatigue cracking beyond Class C, OR
(d) Confirmed catastrophic over-torque event.

This two-condition replacement pathway is the analog of Cascadia Standard MS-2025-03 §5.4 and is explicitly aligned with it.

4.3 **Generator Replacement.** On insulation failure < 5 MΩ, winding-resistance imbalance > 5%, or repeated bearing thermal trips.

4.4 **Main Bearing.** Vibration MP-1 or MP-2 > 5.0 mm/s RMS sustained, or visible spalling.

---

## Section 5 — Approved Parts & Materials

5.1 **Replacement Parts (selected).**

| Part Number | Description |
|---|---|
| VS-VG2-GB-345-FL | Full gearbox assembly, 3.45 MW |
| VS-VG2-HSS-BRG | HSS bearing kit |
| VS-VG2-PL1-BRG | Planetary stage 1 bearing kit |
| VS-PMG-345-FL | Generator assembly, 3.45 MW PMG (V117) |
| VS-DFIG-345-FL | Generator assembly, 3.45 MW DFIG (V112) |
| VS-COOL-OC-V3 | Oil-cooler heat-exchanger, V3 |
| VS-YAW-DRV-A4 | Yaw drive motor, A4 revision |

5.2 **Refurbishment Parts.** Vestas-certified refurbishment kits are listed under VS-RFB-* part numbers and are warrantied for 24 months from installation. Use of Vestas-certified refurbishment kits preserves Extended Service Contract coverage.

5.3 **Gearbox Lubricant.** Castrol Optigear Synthetic X 320 or Vestas-approved equivalent.

5.4 **Fastener Torque (Selected).**
- Main shaft to gearbox flange: **6,200 N·m ± 4%**.
- HSS coupling: **820 N·m ± 4%**.
- Yaw bearing: **2,100 N·m ± 5%**.

---

## Section 6 — Warranty Conditions

6.1 **OEM Warranty.** Standard 5-year initial warranty. Extended Service Contract available.

6.2 **Refurbishment-Preserves-Warranty.** Use of Vestas-certified refurbishment kits (VS-RFB-* part numbers) by Vestas-certified service partners preserves Extended Service Contract coverage. This is a deliberate departure from peer-OEM practice and reflects Vestas' service-engineering judgment that refurbishment in place is the better operational and lifecycle-cost outcome for most degradation modes.

6.3 **Operator-Standard Compatibility.** Where this Manual and an operator-side internal standard (such as Cascadia Standard MS-2025-03) both apply, the more conservative provision governs. Vestas does not require operators to weaken internal standards as a condition of warranty.

6.4 **No Operator-Standard-Conflict Procedure Required.** Because this Manual is written to integrate with Standard MS-2025-03 and analogous internal standards, no conflict-routing mechanism (such as an MOC) is required for routine vibration or cooling-cadence decisions.

---

## Document Control

| Field | Value |
|---|---|
| Document Number | VS-VTM-2025-01 |
| Revision | 2025-01 |
| Effective | January 20, 2025 |
| Approved By | VP, Service Engineering, Vestas Wind Systems A/S |
| Next Scheduled Revision Review | January 2028 |

**Operator Cross-References:**
- Standard MS-2025-03 §3, §5.4, §6 (Cascadia internal — integrated)
- CSM-7 (Cooling System Maintenance Procedure — integrated)
- VRA-2025-001 (CPS as Vestas-certified service partner)
- For contrast: VTM-SIEMENS-GAMESA-4-2, MOC-2025-022, CAR-2025-005, CAR-2025-007
- OIR-2025-006 (MISO-WIND-038 — counter-example reliability profile)
