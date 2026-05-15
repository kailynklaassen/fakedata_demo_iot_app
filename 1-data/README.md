# 1 — Generate Structured Operational Data

Produces 13 correlated source tables (~11.5M rows total) representing a year of renewable energy operations for a fictional utility.

## What it creates

| Table | Approx. rows | Description |
| --- | --- | --- |
| `regions` | 8 | US ISO regions (CAISO, ERCOT, NW-PowerPool, …) |
| `sites` | 40 | Physical generation sites |
| `assets` | 650 | Individual monitored equipment (wind turbines, inverters, batteries, transformers, substation gear) |
| `technicians` | 300 | Field maintenance workforce |
| `market_prices` | 70,080 | Hourly LMP per region, with seasonal + diurnal patterns |
| `telemetry` | 10,512,000 | 5-min IoT sensor readings for 100 high-frequency assets |
| `sensor_anomalies` | ~4,300 | Anomalies derived from telemetry |
| `outages` | ~3,900 | Forced + planned outages |
| `maintenance_schedule` | ~4,600 | Quarterly + annual scheduled work |
| `work_orders` | ~6,300 | Preventive / reactive / emergency / inspection WOs |
| `asset_financials` | 237,250 | Daily P&L per asset |
| `power_sales` | 350,400 | Hourly per-site energy sales |
| `safety_incidents` | 2,000 | Workplace safety events |

## Causal chains baked in

The data is **correlated, not random**:

- `asset.health_profile` (healthy / degrading / high_risk / failure_prone, internal to generator) drives:
  - telemetry drift (temperature, vibration, efficiency)
  - failure event frequency
- Telemetry events → `sensor_anomalies` → `outages` (probability scales with severity)
- `outages` → emergency `work_orders` + `asset_financials` revenue loss
- `maintenance_schedule.completed_flag` → outage probability (skipped maintenance increases failures)
- `market_prices` have summer peak + evening peak → outages during high-price hours create larger revenue loss
- `safety_incidents` cluster ~30% around emergency work orders

## Pre-requisites

```bash
# CLI auth (replace profile name as needed)
databricks auth login https://<your-workspace>.cloud.databricks.com --profile=<profile>

# Python 3.12 + uv
brew install uv   # macOS
```

## Configure

Edit the constants near the top of `generate.py`:

```python
CATALOG = "serverless_stable_cgxfyd_catalog"   # <-- your catalog
SCHEMA = "kailyn_klaassen"                      # <-- your schema (will be created if missing)
PROFILE = "fe-vm-serverless-stable-cgxfyd"      # <-- your CLI profile
SEED = 42
```

## Run

**Option A — as a Databricks notebook:** Import `generate.ipynb` into your workspace and Run All. The notebook uses the workspace's serverless spark context.

**Option B — locally via uv:**

```bash
uv run --python 3.12 \
  --with polars --with numpy --with mimesis --with pandas \
  --with 'databricks-connect>=16.4,<17.0' \
  generate.py
```

Runtime: **15-25 minutes** (most of it is the 10M telemetry rows being written in chunks of 5 assets at a time). Output prints per-batch progress.

The script will:
1. Create the schema if it doesn't exist
2. Build the Spark Connect session against serverless compute
3. Write all 13 tables (with `mode='overwrite'`)
4. Validate FK orphans at the end (all should be 0)

## Validate

```bash
uv run --python 3.12 --with 'databricks-connect>=16.4,<17.0' sanity_sql.py
```

Runs 12 sanity SQL queries against the data — checks asset distribution, market price seasonality, anomaly → outage correlation, lost-revenue impact at high price hours, and asset-age vs financials. Useful as a smoke test that the demo's signals will be discoverable.

## Common adjustments

| Want to change | What to edit |
| --- | --- |
| Year (2025 → other) | `YEAR_START` / `YEAR_END` near the top of `generate.py` |
| Number of high-frequency telemetry assets | `hf_assets = candidates_sorted[:100]` in Phase 3 |
| Telemetry interval | `np.timedelta64(5, "m")` to `np.timedelta64(15, "m")` etc. |
| Health profile distribution | `PROFILE_PARAMS` dict |
| Vendor names | `ASSET_PLAN` (manufacturers list per asset type) |
