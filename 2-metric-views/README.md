# 2 — Build Rollup Tables + 4 Metric Views

Builds a clean semantic layer on top of the 13 raw tables.

## What gets created

### Rollup tables (real Delta tables — Genie can query directly)

| Table | Rows | Grain |
| --- | --- | --- |
| `asset_daily_summary` | ~237,250 | one row per asset per day, denormalized signals from telemetry, outages, anomalies, work orders, financials, maintenance |
| `region_daily_summary` | ~5,800 | one row per region × generation_type × day, including safety incidents |

### Unity Catalog Metric Views (declarative YAML)

| View | Source | Measures | Purpose |
| --- | --- | --- | --- |
| `grid_operations_metrics` | `asset_daily_summary` + dim joins | 15 | Operational health, reliability, MTBF/MTTR, capacity factor, grid instability score |
| `financial_performance_metrics` | `asset_daily_summary` + dim joins | 9 | Revenue, OpEx, margin, curtailment, revenue loss from outages, market exposure |
| `maintenance_workforce_metrics` | `work_orders` + dim joins | 15 | Work order types, preventive : reactive ratio, technician utilization, parts cost |
| `executive_summary_metrics` | `region_daily_summary` | 16 | Region-level executive rollups + safety, derived health/risk classifications |

Each view exposes **dimensions** (region_name, asset_type, generation_type, asset_health_status, profitability_band, …) and **measures** (use `MEASURE(measure_name)` when querying).

## Configure

Same constants as step 1 — edit `build_metric_views.py`:
```python
CAT = "serverless_stable_cgxfyd_catalog"
SCH = "kailyn_klaassen"
PROFILE = "fe-vm-serverless-stable-cgxfyd"
```

## Run

**Option A — as a Databricks notebook:** import `build_metric_views.ipynb` and Run All.

**Option B — locally via uv:**

```bash
uv run --python 3.12 --with 'databricks-connect>=16.4,<17.0' build_metric_views.py
```

Runtime: ~2-3 minutes. Creates the 2 rollup tables (via Spark SQL aggregations over the 10M-row telemetry table), then issues 4 `CREATE OR REPLACE VIEW ... WITH METRICS LANGUAGE YAML AS $$ ... $$` statements.

## Validate every measure

Either run `test_metric_views.ipynb` in the workspace, or locally:

```bash
uv run --python 3.12 --with 'databricks-connect>=16.4,<17.0' test_metric_views.py
```

Runs each measure with multiple grouping dimensions, prints OK/WARN/ERROR per measure, then a final summary. Expected: **52 OK / 3 expected zeros / 0 errors**. The 3 "zeros" are correct (e.g., `preventive_maintenance_count` is 0 when grouped by `work_order_type='emergency'`).

## Query pattern (for downstream consumers)

```sql
SELECT
  region_name,
  MEASURE(forced_outage_count) AS forced_outages,
  MEASURE(revenue_loss_from_outages_usd) AS revenue_loss
FROM serverless_stable_cgxfyd_catalog.kailyn_klaassen.financial_performance_metrics
GROUP BY region_name
ORDER BY revenue_loss DESC;
```

The `MEASURE()` function is mandatory in metric view queries — Spark applies the measure's aggregation logic from the view definition.

## Notes

- Metric views support `GROUP BY ALL` for convenience.
- Materialization (pre-computed aggregations) is NOT enabled in this script. Add a `materialization:` block to any metric view YAML if you want sub-second Genie response times on common groupings.
- Capacity factor is computed only across telemetry-bearing generation assets to avoid biasing the denominator with non-generating equipment.
