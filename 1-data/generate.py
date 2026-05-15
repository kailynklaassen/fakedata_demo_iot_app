"""
Renewable Energy Operational Data Generator
Approved plan 2026-05-13. Target: serverless_stable_cgxfyd_catalog.kailyn_klaassen

13 tables with enforced causal chains:
  asset health profile -> telemetry drift -> sensor_anomalies ->
  outages -> work_orders -> asset_financials revenue impact
"""

import os
import time
import numpy as np
import polars as pl
import pandas as pd
from mimesis import Generic
from mimesis.locales import Locale
from databricks.connect import DatabricksSession

CATALOG = "serverless_stable_cgxfyd_catalog"
SCHEMA = "kailyn_klaassen"
PROFILE = "fe-vm-serverless-stable-cgxfyd"
SEED = 42

os.environ["DATABRICKS_CONFIG_PROFILE"] = PROFILE
rng = np.random.default_rng(SEED)
g = Generic(locale=Locale.EN, seed=SEED)

YEAR_START = np.datetime64("2025-01-01")
YEAR_END = np.datetime64("2025-12-31")

print("Building Databricks Connect (serverless) session...")
spark = DatabricksSession.builder.profile(PROFILE).serverless().getOrCreate()
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")
print(f"Target: {CATALOG}.{SCHEMA}\n")


def write_delta(df: pl.DataFrame, table: str, mode: str = "overwrite") -> None:
    pdf = df.to_pandas()
    sdf = spark.createDataFrame(pdf)
    writer = sdf.write.format("delta").mode(mode)
    if mode == "overwrite":
        writer = writer.option("overwriteSchema", "true")
    writer.saveAsTable(f"{CATALOG}.{SCHEMA}.{table}")
    print(f"  wrote {table} ({mode}): {df.height:,} rows")


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


# ============================================================
# PHASE 1: BASE ENTITIES
# ============================================================
print("=== Phase 1: Base entities ===")

REGION_NAMES = ["CAISO", "ERCOT", "MISO", "PJM", "NYISO", "SPP", "NW-PowerPool", "SE-Reliability"]
N_REGIONS = len(REGION_NAMES)
regions = pl.DataFrame({
    "region_id": np.arange(1, N_REGIONS + 1, dtype=np.int32),
    "region_name": REGION_NAMES,
})
write_delta(regions, "regions")

# --- sites ---
N_SITES = 40
site_ids = np.arange(1001, 1001 + N_SITES, dtype=np.int32)
region_weights = np.array([3, 3, 1.5, 2, 1, 1, 1.5, 1], dtype=np.float64)
region_weights /= region_weights.sum()
site_region_ids = rng.choice(np.arange(1, N_REGIONS + 1), size=N_SITES, p=region_weights).astype(np.int32)
gen_types = rng.choice(["solar", "wind", "battery"], size=N_SITES, p=[0.50, 0.35, 0.15])
capacities = np.array([
    rng.uniform(50, 300) if gt == "solar"
    else rng.uniform(100, 500) if gt == "wind"
    else rng.uniform(20, 150)
    for gt in gen_types
])
capacities = np.round(capacities, 2)
commission_start = np.datetime64("2010-01-01")
commission_span = (np.datetime64("2023-12-31") - commission_start).astype(int)
commission_dates = commission_start + rng.integers(0, commission_span + 1, size=N_SITES).astype("timedelta64[D]")
site_names = [f"{REGION_NAMES[site_region_ids[i] - 1]}-{gen_types[i].upper()}-{i+1:03d}" for i in range(N_SITES)]

sites = pl.DataFrame({
    "site_id": site_ids,
    "region_id": site_region_ids,
    "site_name": site_names,
    "generation_type": gen_types,
    "capacity_mw": capacities,
    "commission_date": commission_dates,
})
write_delta(sites, "sites")

# --- assets ---
ASSET_PLAN = [
    ("wind_turbine", 150, ["Vestas", "GE", "Siemens Gamesa", "Nordex"], 22, 4.0),
    ("inverter", 300, ["SMA", "Enphase", "SolarEdge", "Sungrow"], 12, 3.5),
    ("battery_unit", 100, ["Tesla", "LG Chem", "CATL", "Fluence"], 10, 5.5),
    ("transformer", 50, ["ABB", "Siemens", "Schneider"], 35, 8.0),
    ("substation_equipment", 50, ["ABB", "GE Grid", "Hitachi Energy"], 30, 7.5),
]
TOTAL_ASSETS = sum(p[1] for p in ASSET_PLAN)
site_solar = site_ids[gen_types == "solar"]
site_wind = site_ids[gen_types == "wind"]
site_battery = site_ids[gen_types == "battery"]
site_any = site_ids

asset_rows = []
running_id = 10001
for atype, count, mfrs, life, base_crit in ASSET_PLAN:
    if atype == "wind_turbine":
        pool = site_wind if len(site_wind) else site_any
    elif atype == "inverter":
        pool = site_solar if len(site_solar) else site_any
    elif atype == "battery_unit":
        pool = site_battery if len(site_battery) else site_any
    else:
        pool = site_any
    for _ in range(count):
        a_site = int(rng.choice(pool))
        site_idx = int(np.where(site_ids == a_site)[0][0])
        commission = commission_dates[site_idx]
        install_offset = int(rng.integers(-15, 60))
        install_date = commission + np.timedelta64(install_offset, "D")
        exp_life = int(life + rng.integers(-3, 4))
        crit = float(np.clip(rng.normal(base_crit, 1.5), 1.0, 10.0))
        asset_rows.append({
            "asset_id": running_id,
            "site_id": a_site,
            "asset_tag": f"{atype.upper()[:3]}-{running_id:05d}",
            "asset_type": atype,
            "manufacturer": str(rng.choice(mfrs)),
            "install_date": install_date,
            "expected_life_years": exp_life,
            "criticality_score": round(crit, 2),
        })
        running_id += 1

asset_ids = np.array([a["asset_id"] for a in asset_rows], dtype=np.int32)
profile_choices = rng.choice(
    ["healthy", "degrading", "high_risk", "failure_prone"],
    size=TOTAL_ASSETS, p=[0.50, 0.25, 0.15, 0.10]
)
assets_pd = pd.DataFrame(asset_rows)
assets_pd["install_date"] = pd.to_datetime(assets_pd["install_date"]).dt.date
assets = pl.from_pandas(assets_pd)
write_delta(assets, "assets")

asset_health = dict(zip(asset_ids.tolist(), profile_choices.tolist()))
asset_site = {a["asset_id"]: a["site_id"] for a in asset_rows}
asset_type = {a["asset_id"]: a["asset_type"] for a in asset_rows}
asset_crit = {a["asset_id"]: a["criticality_score"] for a in asset_rows}
site_region = dict(zip(site_ids.tolist(), site_region_ids.tolist()))
site_capacity = dict(zip(site_ids.tolist(), capacities.tolist()))
site_gen_type = dict(zip(site_ids.tolist(), gen_types.tolist()))

# Count assets per site (used for per-asset capacity slicing)
assets_per_site = {}
for aid in asset_ids:
    s = asset_site[int(aid)]
    assets_per_site[s] = assets_per_site.get(s, 0) + 1

# --- technicians ---
N_TECHS = 300
pool_n = 1000
_first = np.array([g.person.first_name() for _ in range(pool_n)])
_last = np.array([g.person.last_name() for _ in range(pool_n)])
tech_names = [f"{_first[rng.integers(0, pool_n)]} {_last[rng.integers(0, pool_n)]}" for _ in range(N_TECHS)]
cert_levels = rng.choice(["Junior", "Mid", "Senior", "Master"], size=N_TECHS, p=[0.30, 0.45, 0.20, 0.05])
hire_start = np.datetime64("2015-01-01")
hire_span = (np.datetime64("2024-12-31") - hire_start).astype(int)
tech_region_ids = rng.integers(1, N_REGIONS + 1, size=N_TECHS).astype(np.int32)
tech_ids = np.arange(20001, 20001 + N_TECHS, dtype=np.int32)
hire_dates = hire_start + rng.integers(0, hire_span + 1, size=N_TECHS).astype("timedelta64[D]")
technicians_pd = pd.DataFrame({
    "technician_id": tech_ids,
    "region_id": tech_region_ids,
    "technician_name": tech_names,
    "certification_level": cert_levels,
    "hire_date": pd.to_datetime(hire_dates).date,
})
technicians = pl.from_pandas(technicians_pd)
write_delta(technicians, "technicians")

tech_region = dict(zip(tech_ids.tolist(), tech_region_ids.tolist()))
tech_ids_by_region = {}
for tid, rid in tech_region.items():
    tech_ids_by_region.setdefault(rid, []).append(tid)


# ============================================================
# PHASE 2: MARKET PRICES
# ============================================================
print("\n=== Phase 2: Market prices ===")
hourly_ts = np.arange(
    YEAR_START.astype("datetime64[h]"),
    (YEAR_END + np.timedelta64(1, "D")).astype("datetime64[h]"),
    np.timedelta64(1, "h"),
)
n_hours = len(hourly_ts)
print(f"  hourly timestamps: {n_hours:,}")

region_price_base = {1: 1.20, 2: 1.10, 3: 0.95, 4: 1.05, 5: 1.10, 6: 0.92, 7: 0.90, 8: 1.00}
rows_mp = n_hours * N_REGIONS
mp_region_ids = np.repeat(np.arange(1, N_REGIONS + 1), n_hours).astype(np.int32)
mp_ts = np.tile(hourly_ts, N_REGIONS)
day_of_year = ((mp_ts.astype("datetime64[D]") - np.datetime64("2025-01-01")).astype(int)) % 365
season_factor = 1.0 + 0.4 * np.sin(2 * np.pi * (day_of_year - 100) / 365)
hours_of_day = mp_ts.astype("datetime64[h]").astype(int) % 24
hour_factor = 1.0 + 0.3 * np.exp(-((hours_of_day - 19) ** 2) / 6.0) + 0.1 * np.exp(-((hours_of_day - 8) ** 2) / 4.0)
base_price = 40.0
region_multipliers = np.array([region_price_base[r] for r in mp_region_ids])
noise = rng.normal(0, 3.0, size=rows_mp)
real_time_price = np.round(base_price * season_factor * hour_factor * region_multipliers + noise, 2)
dayahead_price = np.round(real_time_price + rng.normal(0, 2.5, size=rows_mp), 2)
demand_forecast = np.round(5000 * season_factor * hour_factor + rng.normal(0, 200, size=rows_mp), 1)

market_prices = pl.DataFrame({
    "market_price_id": np.arange(1, rows_mp + 1, dtype=np.int64),
    "region_id": mp_region_ids,
    "timestamp": mp_ts.astype("datetime64[us]"),
    "real_time_price_mwh": real_time_price.astype(np.float32),
    "dayahead_price_mwh": dayahead_price.astype(np.float32),
    "demand_forecast_mw": demand_forecast.astype(np.float32),
})
write_delta(market_prices, "market_prices")

# Lookup: region_id -> hourly price array (length n_hours)
mp_lookup = {r: real_time_price[mp_region_ids == r] for r in range(1, N_REGIONS + 1)}
# Region daily avg price
mp_daily_avg = {r: mp_lookup[r].reshape(-1, 24).mean(axis=1) for r in range(1, N_REGIONS + 1)}


# ============================================================
# PHASE 3: TELEMETRY (chunked)
# ============================================================
print("\n=== Phase 3: Telemetry ===")
candidates = [int(aid) for aid in asset_ids if asset_type[int(aid)] in ("wind_turbine", "inverter", "battery_unit")]
candidates_sorted = sorted(candidates, key=lambda a: -asset_crit[a])
hf_assets = candidates_sorted[:100]
print(f"  high-frequency assets: {len(hf_assets)}")

telemetry_ts = np.arange(
    YEAR_START.astype("datetime64[m]"),
    (YEAR_END + np.timedelta64(1, "D")).astype("datetime64[m]"),
    np.timedelta64(5, "m"),
)
telemetry_ts_us = telemetry_ts.astype("datetime64[us]")
n_per_asset = len(telemetry_ts)
print(f"  intervals per asset: {n_per_asset:,}")

PROFILE_PARAMS = {
    "healthy":       {"temp_drift": 0.0, "vib_drift": 0.0, "events_per_year": 0,  "eff_decline": 0.01, "voltage_inst": 0},
    "degrading":     {"temp_drift": 2.5, "vib_drift": 0.3, "events_per_year": 3,  "eff_decline": 0.05, "voltage_inst": 1},
    "high_risk":     {"temp_drift": 5.0, "vib_drift": 0.7, "events_per_year": 6,  "eff_decline": 0.10, "voltage_inst": 3},
    "failure_prone": {"temp_drift": 8.0, "vib_drift": 1.2, "events_per_year": 12, "eff_decline": 0.18, "voltage_inst": 6},
}

event_records = []
telemetry_id_counter = 1
batch_size = 5
batch_buffer = []
batches_written = 0
total_rows = 0
start_time = time.time()

time_secs = np.arange(n_per_asset, dtype=np.int64) * 300
hour_of_day_t = (time_secs // 3600) % 24
day_progress = (time_secs % 86400) / 86400.0
t_frac = np.linspace(0, 1, n_per_asset, dtype=np.float32)
seasonal = np.sin(2 * np.pi * (t_frac - 0.4))
daily_curve = np.sin(2 * np.pi * (day_progress - 0.25))

for asset_idx, aid in enumerate(hf_assets):
    profile = asset_health[aid]
    params = PROFILE_PARAMS[profile]
    atype = asset_type[aid]
    site_id = asset_site[aid]
    a_capacity = site_capacity[site_id] / max(1, assets_per_site[site_id])
    a_rng = np.random.default_rng(SEED + aid)
    n = n_per_asset

    # Capacity factor by type
    if atype == "inverter":
        cf = np.clip(daily_curve * (0.7 + 0.3 * (seasonal + 1) / 2), 0, 1)
    elif atype == "wind_turbine":
        cf = np.clip(0.35 + 0.15 * (-seasonal) + 0.2 * a_rng.normal(0, 1, n), 0, 1)
    else:  # battery
        cf = 0.4 + 0.3 * np.sin(2 * np.pi * day_progress * 2)
        cf = np.clip(cf, 0, 1)

    power_output = a_capacity * cf

    voltage = 480.0 + a_rng.normal(0, 2, n)
    current = power_output * 1000 / 480.0 + a_rng.normal(0, 5, n)
    temp = 35.0 + 10 * seasonal + 8 * daily_curve + a_rng.normal(0, 1, n)
    vibration_base = 1.5 if atype == "wind_turbine" else 0.3 if atype == "transformer" else 0.1
    vibration = vibration_base + a_rng.normal(0, 0.1, n)

    temp = temp + params["temp_drift"] * t_frac
    vibration = vibration + params["vib_drift"] * t_frac
    efficiency = (96.0 - params["eff_decline"] * 100 * t_frac) + a_rng.normal(0, 0.5, n)
    efficiency = np.clip(efficiency, 60, 99)

    # Inject failure events
    n_events = params["events_per_year"]
    if n_events > 0:
        event_starts = a_rng.integers(100, n - 100, size=n_events)
        for es in sorted(event_starts):
            dur = int(a_rng.integers(12, 73))
            end_idx = min(es + dur, n - 1)
            severity = float(a_rng.uniform(5, 10))
            spike_temp = a_rng.uniform(8, 25)
            has_vib_spike = atype in ("wind_turbine", "transformer")
            spike_vib = a_rng.uniform(1.0, 3.5) if has_vib_spike else 0.0
            temp[es:end_idx] += spike_temp
            vibration[es:end_idx] += spike_vib
            efficiency[es:end_idx] -= a_rng.uniform(10, 25)
            if has_vib_spike and a_rng.random() < 0.5:
                anom_type = "vibration_excess"
            elif a_rng.random() < 0.3:
                anom_type = "efficiency_decline"
            else:
                anom_type = "overheating"
            event_records.append({
                "asset_id": int(aid),
                "timestamp": telemetry_ts[int(es)],
                "anomaly_type": anom_type,
                "severity_score": round(severity, 2),
                "predicted_failure_probability": round(float(sigmoid((severity - 5) * 0.5)), 4),
            })

    # Voltage instability windows
    for _ in range(params["voltage_inst"]):
        v_start = int(a_rng.integers(0, n - 300))
        v_dur = int(a_rng.integers(50, 300))
        voltage[v_start:v_start + v_dur] += a_rng.normal(0, 15, v_dur)
        event_records.append({
            "asset_id": int(aid),
            "timestamp": telemetry_ts[v_start],
            "anomaly_type": "voltage_instability",
            "severity_score": round(float(a_rng.uniform(4, 9)), 2),
            "predicted_failure_probability": round(float(a_rng.uniform(0.2, 0.85)), 4),
        })

    if atype == "battery_unit":
        soc = 50 + 35 * np.sin(2 * np.pi * day_progress * 2) + a_rng.normal(0, 3, n)
        soc = np.clip(soc, 5, 100)
    else:
        soc = np.full(n, np.nan)

    alarm = (temp > 70.0) | (vibration > 4.0)
    tel_ids = np.arange(telemetry_id_counter, telemetry_id_counter + n, dtype=np.int64)
    telemetry_id_counter += n

    asset_df = pl.DataFrame({
        "telemetry_id": tel_ids,
        "asset_id": np.full(n, aid, dtype=np.int32),
        "timestamp": telemetry_ts_us,
        "voltage": np.round(voltage, 2).astype(np.float32),
        "current": np.round(current, 2).astype(np.float32),
        "temperature": np.round(temp, 2).astype(np.float32),
        "vibration": np.round(vibration, 3).astype(np.float32),
        "power_output_mw": np.round(power_output, 3).astype(np.float32),
        "state_of_charge": np.round(soc, 1).astype(np.float32),
        "efficiency_pct": np.round(efficiency, 2).astype(np.float32),
        "alarm_flag": alarm,
    })
    batch_buffer.append(asset_df)

    if len(batch_buffer) >= batch_size:
        chunk = pl.concat(batch_buffer)
        write_delta(chunk, "telemetry", mode="overwrite" if batches_written == 0 else "append")
        total_rows += chunk.height
        batches_written += 1
        batch_buffer = []
        elapsed = time.time() - start_time
        print(f"  [{asset_idx+1}/{len(hf_assets)}] telemetry total: {total_rows:,} rows ({elapsed:.1f}s)")

if batch_buffer:
    chunk = pl.concat(batch_buffer)
    write_delta(chunk, "telemetry", mode="overwrite" if batches_written == 0 else "append")
    total_rows += chunk.height
print(f"  telemetry final: {total_rows:,} rows")


# ============================================================
# PHASE 4: DERIVED EVENTS
# ============================================================
print("\n=== Phase 4: Derived events ===")

# --- sensor_anomalies (telemetry-driven + baseline for non-HF assets) ---
extra_anomalies = []
extra_per_profile = {"healthy": 1, "degrading": 5, "high_risk": 15, "failure_prone": 30}
for aid in asset_ids:
    aid_int = int(aid)
    if aid_int in hf_assets:
        continue
    n_extra = extra_per_profile[asset_health[aid_int]]
    for _ in range(n_extra):
        ts = YEAR_START + np.timedelta64(int(rng.integers(0, 365 * 24 * 60)), "m")
        severity = float(rng.uniform(2, 9))
        extra_anomalies.append({
            "asset_id": aid_int,
            "timestamp": ts,
            "anomaly_type": str(rng.choice(["overheating", "voltage_instability", "vibration_excess", "efficiency_decline", "soc_drift"])),
            "severity_score": round(severity, 2),
            "predicted_failure_probability": round(float(sigmoid((severity - 5) * 0.4)), 4),
        })

all_anomalies = event_records + extra_anomalies
print(f"  total anomalies: {len(all_anomalies):,}")
anom_pd = pd.DataFrame(all_anomalies)
anom_pd.insert(0, "anomaly_id", np.arange(1, len(anom_pd) + 1, dtype=np.int64))
anom_df = pl.from_pandas(anom_pd)
write_delta(anom_df, "sensor_anomalies")

# --- outages ---
outage_rows = []
outage_id = 1
for a in all_anomalies:
    p_out = sigmoid(a["severity_score"] - 6.5)
    if rng.random() < p_out:
        lag = int(rng.uniform(0, 48))
        outage_start = a["timestamp"] + np.timedelta64(lag, "h")
        sev_norm = max(0.0, (a["severity_score"] - 5) / 5)
        dur_h = int(np.clip(2 + sev_norm * 336 * rng.random(), 1, 336))
        outage_end = outage_start + np.timedelta64(dur_h, "h")
        aid = a["asset_id"]
        s_id = asset_site[aid]
        a_cap = site_capacity[s_id] / max(1, assets_per_site[s_id])
        outage_rows.append({
            "outage_id": outage_id,
            "asset_id": aid,
            "site_id": s_id,
            "outage_start_ts": outage_start,
            "outage_end_ts": outage_end,
            "outage_reason": a["anomaly_type"],
            "forced_outage_flag": True,
            "lost_generation_mwh": round(dur_h * a_cap * 0.35, 2),
        })
        outage_id += 1

# Baseline planned outages
baseline_per_profile = {"healthy": 2, "degrading": 4, "high_risk": 5, "failure_prone": 7}
for aid in asset_ids:
    aid_int = int(aid)
    n_b = baseline_per_profile[asset_health[aid_int]]
    for _ in range(n_b):
        ts = YEAR_START + np.timedelta64(int(rng.integers(0, 365 * 24 * 60)), "m")
        dur_h = int(rng.uniform(2, 48))
        s_id = asset_site[aid_int]
        a_cap = site_capacity[s_id] / max(1, assets_per_site[s_id])
        outage_rows.append({
            "outage_id": outage_id,
            "asset_id": aid_int,
            "site_id": s_id,
            "outage_start_ts": ts,
            "outage_end_ts": ts + np.timedelta64(dur_h, "h"),
            "outage_reason": str(rng.choice(["scheduled_maintenance", "grid_event", "weather", "manual_shutdown"])),
            "forced_outage_flag": False,
            "lost_generation_mwh": round(dur_h * a_cap * 0.30, 2),
        })
        outage_id += 1

outages_df = pl.from_pandas(pd.DataFrame(outage_rows))
write_delta(outages_df, "outages")
print(f"  outages: {outages_df.height:,}")

# --- maintenance_schedule ---
ms_rows = []
ms_id = 1
completion_per_profile = {"healthy": 0.95, "degrading": 0.85, "high_risk": 0.75, "failure_prone": 0.60}
for aid in asset_ids:
    aid_int = int(aid)
    comp_rate = completion_per_profile[asset_health[aid_int]]
    quarterly = [np.datetime64("2025-01-15") + np.timedelta64(90 * q, "D") for q in range(4)]
    other = [YEAR_START + np.timedelta64(int(rng.integers(0, 365)), "D") for _ in range(int(rng.integers(2, 5)))]
    for d in quarterly:
        completed = bool(rng.random() < comp_rate)
        ms_rows.append({
            "schedule_id": ms_id,
            "asset_id": aid_int,
            "planned_date": d,
            "maintenance_type": "quarterly_inspection",
            "completed_flag": completed,
            "overdue_flag": (not completed) and (d < np.datetime64("2025-12-31")),
        })
        ms_id += 1
    for d in other:
        completed = bool(rng.random() < comp_rate)
        ms_rows.append({
            "schedule_id": ms_id,
            "asset_id": aid_int,
            "planned_date": d,
            "maintenance_type": str(rng.choice(["annual_overhaul", "oil_change", "firmware_update"])),
            "completed_flag": completed,
            "overdue_flag": (not completed) and (d < np.datetime64("2025-12-31")),
        })
        ms_id += 1

ms_pd = pd.DataFrame(ms_rows)
ms_pd["planned_date"] = pd.to_datetime(ms_pd["planned_date"]).dt.date
ms_df = pl.from_pandas(ms_pd)
write_delta(ms_df, "maintenance_schedule")
print(f"  maintenance_schedule: {ms_df.height:,}")

# --- work_orders ---
wo_rows = []
wo_id = 1
for o in outage_rows:
    s_id = o["site_id"]
    region = site_region[s_id]
    techs = tech_ids_by_region.get(region) or list(tech_region.keys())
    tech = int(rng.choice(techs))
    dur_h = int((o["outage_end_ts"] - o["outage_start_ts"]).astype("timedelta64[h]").astype(int))
    if o["forced_outage_flag"]:
        wo_type = "emergency" if dur_h > 24 else "reactive"
        outage_link = o["outage_id"]
        if wo_type == "emergency":
            labor = float(rng.uniform(8, 80)); parts = float(rng.uniform(5000, 200000)); priority = "P1"
        else:
            labor = float(rng.uniform(4, 24)); parts = float(rng.uniform(500, 25000)); priority = "P2"
    else:
        wo_type = "preventive"
        outage_link = None
        labor = float(rng.uniform(2, 8)); parts = float(rng.uniform(200, 5000)); priority = "P3"
    created = o["outage_start_ts"] + np.timedelta64(int(rng.integers(0, 4)), "h")
    completed = created + np.timedelta64(int(labor + rng.integers(0, 24)), "h")
    status = str(rng.choice(["completed", "in_progress", "cancelled"], p=[0.85, 0.10, 0.05]))
    wo_rows.append({
        "work_order_id": wo_id, "asset_id": o["asset_id"], "technician_id": tech,
        "outage_id": outage_link, "work_order_type": wo_type, "priority": priority,
        "created_ts": created, "completed_ts": completed,
        "labor_hours": round(labor, 2), "parts_cost_usd": round(parts, 2), "status": status,
    })
    wo_id += 1

for ms in ms_rows:
    if not ms["completed_flag"] or rng.random() > 0.6:
        continue
    aid = ms["asset_id"]
    s_id = asset_site[aid]
    region = site_region[s_id]
    techs = tech_ids_by_region.get(region) or list(tech_region.keys())
    tech = int(rng.choice(techs))
    wo_type = "inspection" if "inspection" in ms["maintenance_type"] else "preventive"
    priority = "P4" if wo_type == "inspection" else "P3"
    created = np.datetime64(ms["planned_date"]).astype("datetime64[s]") + np.timedelta64(int(rng.integers(-4, 24)), "h")
    labor = float(rng.uniform(1, 12)); parts = float(rng.uniform(100, 3000))
    completed = created + np.timedelta64(int(labor + rng.integers(0, 4)), "h")
    wo_rows.append({
        "work_order_id": wo_id, "asset_id": aid, "technician_id": tech,
        "outage_id": None, "work_order_type": wo_type, "priority": priority,
        "created_ts": created, "completed_ts": completed,
        "labor_hours": round(labor, 2), "parts_cost_usd": round(parts, 2), "status": "completed",
    })
    wo_id += 1

wo_pd = pd.DataFrame(wo_rows)
wo_pd["outage_id"] = wo_pd["outage_id"].astype("Int64")
wo_df = pl.from_pandas(wo_pd)
write_delta(wo_df, "work_orders")
print(f"  work_orders: {wo_df.height:,}")


# ============================================================
# PHASE 5: FINANCIALS
# ============================================================
print("\n=== Phase 5: Financials ===")

days = np.arange(YEAR_START, YEAR_END + np.timedelta64(1, "D"), np.timedelta64(1, "D"))
n_days = len(days)

# Pre-aggregate per-day outage loss and per-day work order cost per asset
outage_day_loss = {}
for o in outage_rows:
    start = o["outage_start_ts"].astype("datetime64[D]")
    end = o["outage_end_ts"].astype("datetime64[D]")
    span = np.arange(start, end + np.timedelta64(1, "D"))
    if len(span) == 0:
        continue
    per_day = o["lost_generation_mwh"] / len(span)
    for d in span:
        key = (o["asset_id"], np.datetime64(d, "D"))
        outage_day_loss[key] = outage_day_loss.get(key, 0.0) + per_day

wo_day_cost = {}
for w in wo_rows:
    d = w["created_ts"].astype("datetime64[D]")
    key = (w["asset_id"], d)
    wo_day_cost[key] = wo_day_cost.get(key, 0.0) + w["parts_cost_usd"]

base_eff_profile = {"healthy": 0.92, "degrading": 0.85, "high_risk": 0.75, "failure_prone": 0.65}
fin_rows = []
fid = 1
for aid in asset_ids:
    aid_int = int(aid)
    s_id = asset_site[aid_int]
    region = site_region[s_id]
    a_cap = site_capacity[s_id] / max(1, assets_per_site[s_id])
    base_eff = base_eff_profile[asset_health[aid_int]]
    daily_opex = a_cap * 8.0
    for di, d in enumerate(days):
        avg_price = float(mp_daily_avg[region][min(di, 364)])
        gen_mwh = a_cap * 24 * 0.30 * base_eff
        lost = float(outage_day_loss.get((aid_int, d), 0.0))
        net_gen = max(0.0, gen_mwh - lost)
        revenue = round(net_gen * avg_price, 2)
        opex = round(daily_opex + rng.normal(0, daily_opex * 0.05), 2)
        maint = round(float(wo_day_cost.get((aid_int, d), 0.0)), 2)
        curtailed = round(float(rng.uniform(0, 0.15) * gen_mwh) if avg_price < 30 else 0.0, 3)
        margin = round(((revenue - opex - maint) / revenue) * 100, 2) if revenue > 0 else -100.0
        fin_rows.append({
            "financial_id": fid, "asset_id": aid_int, "date": d,
            "revenue_usd": revenue, "opex_usd": opex,
            "maintenance_cost_usd": maint, "profit_margin_pct": margin,
            "curtailed_mwh": curtailed,
        })
        fid += 1

fin_pd = pd.DataFrame(fin_rows)
fin_pd["date"] = pd.to_datetime(fin_pd["date"]).dt.date
fin_df = pl.from_pandas(fin_pd)
write_delta(fin_df, "asset_financials")
print(f"  asset_financials: {fin_df.height:,}")

# --- power_sales ---
print("  building power_sales (hourly per site)...")
site_outage_loss_per_hour = {}
for o in outage_rows:
    start_h = int(((o["outage_start_ts"] - np.datetime64("2025-01-01T00:00:00")) / np.timedelta64(1, "h")))
    end_h = int(((o["outage_end_ts"] - np.datetime64("2025-01-01T00:00:00")) / np.timedelta64(1, "h")))
    start_h = max(0, start_h)
    end_h = min(n_hours - 1, end_h)
    if end_h <= start_h:
        continue
    per_h = o["lost_generation_mwh"] / (end_h - start_h)
    s_id = o["site_id"]
    for h in range(start_h, end_h):
        key = (s_id, h)
        site_outage_loss_per_hour[key] = site_outage_loss_per_hour.get(key, 0.0) + per_h

ps_rows = []
ps_id = 1
for s_id in site_ids:
    s_id_int = int(s_id)
    cap = site_capacity[s_id_int]
    region = site_region[s_id_int]
    gt = site_gen_type[s_id_int]
    prices = mp_lookup[region]
    for h_idx in range(n_hours):
        ts = np.datetime64("2025-01-01T00:00:00") + np.timedelta64(h_idx, "h")
        hour = h_idx % 24
        if gt == "solar":
            cf = max(0.0, np.sin(np.pi * (hour - 6) / 12)) * 0.85
        elif gt == "wind":
            cf = max(0.0, min(1.0, 0.35 + 0.15 * np.sin(2 * np.pi * h_idx / (24 * 7)) + rng.normal(0, 0.05)))
        else:
            cf = max(0.0, min(1.0, 0.4 + 0.3 * np.sin(2 * np.pi * hour / 24 * 2)))
        gen = cap * cf
        lost = site_outage_loss_per_hour.get((s_id_int, h_idx), 0.0)
        net = max(0.0, gen - lost)
        price = float(prices[h_idx])
        ps_rows.append({
            "sale_id": ps_id, "site_id": s_id_int, "timestamp": ts,
            "energy_sold_mwh": round(net, 3),
            "market_price": round(price, 2),
            "total_revenue": round(net * price, 2),
        })
        ps_id += 1

ps_chunk = 100_000
print(f"  power_sales total: {len(ps_rows):,} rows")
for i in range(0, len(ps_rows), ps_chunk):
    chunk_pd = pd.DataFrame(ps_rows[i:i + ps_chunk])
    chunk_df = pl.from_pandas(chunk_pd)
    write_delta(chunk_df, "power_sales", mode="overwrite" if i == 0 else "append")


# ============================================================
# PHASE 6: SAFETY INCIDENTS
# ============================================================
print("\n=== Phase 6: Safety incidents ===")
n_incidents = 2000
emergency_wos = [w for w in wo_rows if w["work_order_type"] == "emergency"]
si_rows = []
for sid in range(1, n_incidents + 1):
    if rng.random() < 0.3 and emergency_wos:
        ewo = emergency_wos[int(rng.integers(0, len(emergency_wos)))]
        aid = ewo["asset_id"]
        s_id = asset_site[aid]
        ts = ewo["created_ts"] + np.timedelta64(int(rng.integers(-2, 6)), "h")
    else:
        s_id = int(rng.choice(site_ids))
        ts = YEAR_START + np.timedelta64(int(rng.integers(0, 365 * 24 * 60)), "m")
    region = site_region[s_id]
    techs = tech_ids_by_region.get(region) or list(tech_region.keys())
    tech = int(rng.choice(techs))
    severity = str(rng.choice(["near_miss", "minor", "recordable", "serious"], p=[0.50, 0.30, 0.15, 0.05]))
    lost_time = severity in ("recordable", "serious") and (rng.random() < 0.8)
    si_rows.append({
        "incident_id": sid, "site_id": s_id, "technician_id": tech,
        "incident_ts": ts, "severity": severity, "lost_time_flag": bool(lost_time),
    })

si_df = pl.from_pandas(pd.DataFrame(si_rows))
write_delta(si_df, "safety_incidents")


# ============================================================
# VALIDATION
# ============================================================
print("\n=== Validation ===")
tables = ["regions", "sites", "assets", "technicians", "market_prices",
          "telemetry", "sensor_anomalies", "outages", "maintenance_schedule",
          "work_orders", "asset_financials", "power_sales", "safety_incidents"]
for t in tables:
    cnt = spark.table(f"{CATALOG}.{SCHEMA}.{t}").count()
    print(f"  {t:25s} {cnt:>12,} rows")

print("\n  FK orphan checks:")
checks = [
    ("sites", "region_id", "regions", "region_id"),
    ("assets", "site_id", "sites", "site_id"),
    ("technicians", "region_id", "regions", "region_id"),
    ("telemetry", "asset_id", "assets", "asset_id"),
    ("sensor_anomalies", "asset_id", "assets", "asset_id"),
    ("outages", "asset_id", "assets", "asset_id"),
    ("outages", "site_id", "sites", "site_id"),
    ("work_orders", "asset_id", "assets", "asset_id"),
    ("work_orders", "technician_id", "technicians", "technician_id"),
    ("market_prices", "region_id", "regions", "region_id"),
    ("maintenance_schedule", "asset_id", "assets", "asset_id"),
    ("asset_financials", "asset_id", "assets", "asset_id"),
    ("power_sales", "site_id", "sites", "site_id"),
    ("safety_incidents", "site_id", "sites", "site_id"),
    ("safety_incidents", "technician_id", "technicians", "technician_id"),
]
for child, ck, parent, pk in checks:
    q = (f"SELECT COUNT(*) AS n FROM {CATALOG}.{SCHEMA}.{child} c "
         f"LEFT JOIN {CATALOG}.{SCHEMA}.{parent} p ON c.{ck} = p.{pk} "
         f"WHERE p.{pk} IS NULL AND c.{ck} IS NOT NULL")
    n = spark.sql(q).collect()[0]["n"]
    status = "OK  " if n == 0 else "FAIL"
    print(f"    [{status}] {child}.{ck} -> {parent}.{pk}: {n} orphans")

spark.stop()
print("\nDone.")
