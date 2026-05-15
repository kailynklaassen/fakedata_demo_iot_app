# GE Renewable Energy 1.5 MW Wind Turbine Operating Manual
## Effective 2023 (Pre-Firmware-Refresh Issue)

**Document Reference:** VTM-GE-RENEWABLE-2023
**Manual Title:** Operating and Maintenance Manual — GE 1.5sle / 1.5xle Wind Turbine
**Revision:** 7.1
**Effective Date:** January 15, 2023
**Supersedes:** Revision 7.0 (March 2020)
**Issuer:** GE Renewable Energy, Onshore Wind, Schenectady, NY
**Distribution Class:** Controlled — Authorized Service Providers, Owner Engineering teams.

**Applicable Equipment Models (and Operator Asset Tags):**
- GE 1.5sle Geared platform — **WIN-10016** (NW-PowerPool-WIND-014)
- GE 1.5xle Geared platform — **WIN-10058** (NW-PowerPool-WIND-014)

---

## Important Notice — Pre-Firmware-Refresh Issue

This Manual was issued in January 2023, prior to the **August 2023 firmware refresh** that updated the turbine controller's temperature-reporting interval and revised the cooling-loop telemetry granularity from one sample per 30 minutes to one sample per 5 minutes. Several inspection cadences described in this Manual, particularly in Section 3 (cooling-system inspections) and Section 4 (thermal trip evaluation), reference reporting behavior that the post-refresh firmware no longer produces.

Operators executing this Manual against post-firmware-refresh units are advised that **the procedural cadences in this Manual are inconsistent with the post-August-2023 deployed firmware**. The discrepancy has been formally raised in Operator's corrective-action system as **CAR-2025-007** ("GE Manual Cooling-System Inspection Cadence Inconsistent with 2023 Firmware Refresh — Pending OEM Manual Reissue").

GE Renewable Energy has indicated that a Revision 7.2 reissue is planned but no firm release date has been published as of the date of this notice (per Operator's most recent vendor outreach, March 2026). Until reissue, Operators are advised to follow their internal Cooling System Maintenance Procedure (CSM-7) and Standard MS-2025-03 for cadence determination, while continuing to honor this Manual's inspection-procedure content and warranty conditions.

---

## Section 1 — Equipment Overview

1.1 The GE 1.5sle and 1.5xle are three-bladed, upwind, horizontal-axis wind turbines with a rated capacity of 1.5 MW. The drivetrain consists of a low-speed main shaft, a three-stage step-up gearbox (one planetary, two parallel), a doubly-fed induction generator, and an integrated yaw and pitch system.

1.2 **Major Components.**
- Main bearing (cylindrical roller)
- Gearbox — GE G3-1.5 family
- Generator — DFIG, 1.5 MW class
- Cooling subsystem (gearbox oil cooler, generator coolant loop, converter coolant loop)
- Yaw drives (4×)
- Pitch system (hydraulic, individual per blade on 1.5sle; electric on 1.5xle)

1.3 **Controller.** The turbine is controlled by the GE Mark VIe controller. As noted above, controller firmware was refreshed in August 2023, changing temperature telemetry granularity. The pre-refresh and post-refresh behaviors are not interoperable for purposes of the cadence references in Section 3 of this Manual.

---

## Section 2 — Maintenance Schedule

2.1 **Mandatory Intervals.**

| Activity | Interval |
|---|---|
| Routine inspection | Every 6 months operational |
| Annual service | Every 12 months operational |
| Cooling system inspection (see Section 3 — affected by firmware refresh) | **Every 18 months operational** (per this Manual; *see firmware-refresh notice above*) |
| Gearbox oil change | Every 36 months operational |
| Generator brush inspection / replacement | Every 12 months operational |
| Pitch hydraulic system inspection (1.5sle) | Every 12 months operational |
| Yaw drive inspection | Every 12 months operational |

2.2 **Note on Cooling System Cadence.** The 18-month interval in §2.1 was set in 2020 based on the pre-refresh firmware's 30-minute temperature-reporting interval, which produced averaged thermal data over an inspection window of approximately 18 months. The post-August-2023 firmware's 5-minute reporting interval produces materially more thermal data per unit time; whether the 18-month cadence remains appropriate has not been formally addressed by GE in a manual reissue. Operators are advised to consult internal standards (CSM-7, MS-2025-03) until Revision 7.2 is issued. Cross-reference: CAR-2025-007.

---

## Section 3 — Inspection Procedures

3.1 **Cooling System Inspection (Procedure GE-WTOM-7.1-§3.1).**

Step-by-step (per this Manual, original 2023 issue):

1. Pull a full thermal log from the Mark VIe controller for the preceding 18 months.
2. Compute the running mean of gearbox oil-cooler outlet temperature over each 30-minute reporting interval.
3. Identify any rolling 7-day windows where the mean exceeds 72°C.
4. Inspect the oil-cooler heat-exchanger plate for fouling using a borescope per Procedure GE-WTOM-7.1-§3.1.4.
5. Confirm coolant flow rate at the converter loop within 18.0 – 22.5 L/min per Procedure GE-WTOM-7.1-§3.1.7.
6. Verify generator coolant loop conductivity ≤ 2.0 µS/cm.

**Post-firmware-refresh deviation:** Step 2's "30-minute reporting interval" no longer corresponds to deployed firmware behavior. Operators have observed that executing Step 2 verbatim on post-refresh telemetry produces an over-smoothed mean that masks short-duration excursions. Operator's CSM-7 procedure §4 substitutes a 5-minute interval consistent with the post-refresh firmware. See CAR-2025-007 §3.

3.2 **Vibration Monitoring.** Broadband RMS at the gearbox high-speed bearing. Alert at 3.5 mm/s; replacement evaluation at 5.0 mm/s.

3.3 **Bearing Temperature Thresholds.** Main bearing: 85°C alert, 95°C trip. Gearbox HSS bearing: 88°C alert, 100°C trip.

3.4 **Generator Insulation Resistance.** Annual megger test at 500 V DC. Acceptable: ≥ 10 MΩ. Marginal: 5–10 MΩ (action required). Failed: < 5 MΩ.

---

## Section 4 — Replacement Criteria

4.1 **Gearbox Replacement.** Recommended on:

(a) Broadband RMS vibration ≥ 5.0 mm/s RMS sustained over 72 hours at HSS bearing;
(b) Oil Fe content above 110 ppm with morphology indicating gear-tooth wear;
(c) Confirmed catastrophic over-torque event.

Refurbishment of the G3-1.5 gearbox is permitted using GE-authorized refurbishment partners; refurbishment specifications are detailed in Service Bulletin GE-WTSB-2021-04.

4.2 **Generator Replacement.** On insulation failure below 5 MΩ or confirmed winding short.

4.3 **Cooling Pump / Heat-Exchanger Replacement.** Per condition-based triggers in §3.1.

---

## Section 5 — Approved Parts & Materials

5.1 **Replacement Parts (selected).**

| Part Number | Description |
|---|---|
| GE-G3-15-GB-FL | Full gearbox assembly, 1.5 MW class |
| GE-G3-15-HSS-BRG | HSS bearing kit |
| GE-DFIG-15-FL | Generator assembly, 1.5 MW DFIG |
| GE-COOL-OC-V2 | Oil-cooler heat-exchanger plate, V2 |
| GE-COOL-PMP-A3 | Coolant pump, A3 revision |
| GE-MARKVIE-CTL-FW | Controller firmware (see firmware-refresh notice) |

5.2 **Gearbox Lubricant.** Mobilgear SHC XMP 320 or GE-approved equivalent.

5.3 **Fastener Torque (Selected).**
- Main shaft to gearbox flange: **5,200 N·m ± 5%**, applied in three passes.
- HSS coupling: **740 N·m ± 5%**.
- Yaw bearing: **1,900 N·m ± 5%**.

---

## Section 6 — Warranty Conditions

6.1 **OEM Warranty.** Standard 5-year initial warranty; the units to which this Manual applies (WIN-10016, WIN-10058) are no longer within initial warranty and are subject to ongoing time-and-materials service.

6.2 **Compliance Requirement.** Continued availability of GE OEM service for these units is conditioned on operation consistent with this Manual, with the firmware-refresh exception noted in the prefatory notice. Operator's documented deviations under CAR-2025-007 are acknowledged and do not constitute breach.

6.3 **Service Bulletins.** Owners are responsible for tracking GE-published Service Bulletins. As of the date of this issue, applicable Service Bulletins include GE-WTSB-2021-04 (refurbishment specs), GE-WTSB-2022-09 (yaw drive lubricant), and GE-WTSB-2023-FW (firmware refresh — the August 2023 update referenced above).

---

## Document Control

| Field | Value |
|---|---|
| Document Number | GE-WTOM-7.1 |
| Revision | 7.1 |
| Effective | January 15, 2023 |
| Approved By | Director, Onshore Wind Service Engineering, GE Renewable Energy |
| Planned Next Revision | 7.2 (date TBD) |

**Operator Cross-References:**
- CSM-7 (Cooling System Maintenance Procedure, Cascadia internal)
- Standard MS-2025-03 (Cascadia Mechanical Standard)
- CAR-2025-007 (open corrective action regarding cadence discrepancy)
- OIR-2025-002 (NW-PowerPool-WIND-014 — WIN-10058 May 2025 outage referencing Section 3 cadence)
