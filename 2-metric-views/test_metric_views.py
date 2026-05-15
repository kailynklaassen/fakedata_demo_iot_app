"""
Validate every measure in every metric view by running queries and inspecting results.
For each view: hit every measure, with at least one meaningful grouping dimension.
"""
import os
from databricks.connect import DatabricksSession

CATALOG = globals().get("CATALOG", "serverless_stable_cgxfyd_catalog")
SCHEMA = globals().get("SCHEMA", "kailyn_klaassen")
PROFILE = globals().get("PROFILE", "fe-vm-serverless-stable-cgxfyd")
os.environ["DATABRICKS_CONFIG_PROFILE"] = PROFILE

spark = DatabricksSession.builder.profile(PROFILE).serverless().getOrCreate()
spark.sql(f"USE {CATALOG}.{SCHEMA}")

GREEN = "\033[92m"
RED = "\033[91m"
YEL = "\033[93m"
RESET = "\033[0m"
results = []  # (view, measure, status, sample_value)


def query(view, dim_sql, measures, group_by="GROUP BY ALL", limit=5, order_by=None):
    measure_sql = ",\n  ".join([f"MEASURE({m}) AS {m}" for m in measures])
    select_parts = [dim_sql] if dim_sql else []
    select_parts.append(measure_sql)
    select_clause = ",\n  ".join(select_parts)
    order = f"ORDER BY {order_by}" if order_by else ""
    sql = f"""
SELECT
  {select_clause}
FROM {CATALOG}.{SCHEMA}.{view}
{group_by}
{order}
LIMIT {limit}
""".strip()
    try:
        df = spark.sql(sql)
        rows = df.collect()
        cols = df.columns
        return rows, cols, None
    except Exception as e:
        return None, None, str(e)


def report(view, measures, rows, err):
    if err:
        for m in measures:
            results.append((view, m, "ERROR", err[:80]))
            print(f"  {RED}[ERR]{RESET} {m}: {err[:100]}")
        return
    if not rows:
        for m in measures:
            results.append((view, m, "EMPTY", None))
            print(f"  {YEL}[EMPTY]{RESET} {m}: no rows")
        return
    # Pick the first row as sample
    sample = rows[0].asDict()
    for m in measures:
        v = sample.get(m)
        try:
            v_num = float(v) if v is not None else None
        except (TypeError, ValueError):
            v_num = None
        if v is None:
            status = "NULL"
            color = YEL
        elif v_num == 0:
            status = "ZERO"
            color = YEL
        else:
            status = "OK"
            color = GREEN
        results.append((view, m, status, v))
        print(f"  {color}[{status}]{RESET} {m} = {v}")


def show_rows(rows, cols, max_rows=5):
    if not rows:
        return
    print("    " + " | ".join(f"{c:>22.22s}" for c in cols))
    for r in rows[:max_rows]:
        d = r.asDict()
        line = []
        for c in cols:
            v = d.get(c)
            line.append(f"{str(v):>22.22s}" if v is not None else f"{'NULL':>22}")
        print("    " + " | ".join(line))


# ============================================================
# grid_operations_metrics
# ============================================================
print(f"\n{'='*70}\nVALIDATING: grid_operations_metrics\n{'='*70}")
go_measures = [
    "avg_temperature", "max_temperature", "avg_vibration", "avg_efficiency_pct",
    "total_power_generated_mwh", "anomaly_count", "outage_count", "forced_outage_count",
    "total_downtime_hours", "mttr_hours", "mtbf_hours", "capacity_factor_pct",
    "alarm_count", "overdue_maintenance_count", "grid_instability_risk_score",
]
print("\n-- All measures grouped by asset_type --")
rows, cols, err = query("grid_operations_metrics", "asset_type", go_measures,
                        group_by="GROUP BY asset_type", order_by="asset_type")
show_rows(rows, cols)
report("grid_operations_metrics", go_measures, rows, err)

print("\n-- Dimensions: asset_health_status × operational_risk_level --")
rows, cols, err = query("grid_operations_metrics", "asset_health_status, operational_risk_level",
                        ["outage_count", "anomaly_count", "avg_efficiency_pct"],
                        group_by="GROUP BY asset_health_status, operational_risk_level",
                        order_by="asset_health_status, operational_risk_level", limit=10)
show_rows(rows, cols, max_rows=10)

print("\n-- Dimension: region_name --")
rows, cols, err = query("grid_operations_metrics", "region_name",
                        ["total_power_generated_mwh", "outage_count", "capacity_factor_pct"],
                        group_by="GROUP BY region_name", order_by="region_name")
show_rows(rows, cols)

print("\n-- Time dim: month --")
rows, cols, err = query("grid_operations_metrics", "month",
                        ["total_power_generated_mwh", "outage_count", "avg_efficiency_pct"],
                        group_by="GROUP BY month", order_by="month", limit=12)
show_rows(rows, cols, max_rows=12)


# ============================================================
# financial_performance_metrics
# ============================================================
print(f"\n{'='*70}\nVALIDATING: financial_performance_metrics\n{'='*70}")
fin_measures = [
    "total_revenue_usd", "total_opex_usd", "total_maintenance_cost_usd",
    "net_profit_usd", "profit_margin_pct", "revenue_loss_from_outages_usd",
    "curtailment_loss_mwh", "revenue_per_mwh", "total_lost_mwh",
]
print("\n-- All measures by region_name --")
rows, cols, err = query("financial_performance_metrics", "region_name", fin_measures,
                        group_by="GROUP BY region_name", order_by="region_name")
show_rows(rows, cols)
report("financial_performance_metrics", fin_measures, rows, err)

print("\n-- Dim: profitability_band --")
rows, cols, err = query("financial_performance_metrics", "profitability_band",
                        ["total_revenue_usd", "net_profit_usd", "profit_margin_pct"],
                        group_by="GROUP BY profitability_band", order_by="profitability_band")
show_rows(rows, cols)

print("\n-- Dim: market_exposure_level --")
rows, cols, err = query("financial_performance_metrics", "market_exposure_level",
                        ["total_revenue_usd", "revenue_per_mwh", "revenue_loss_from_outages_usd"],
                        group_by="GROUP BY market_exposure_level", order_by="market_exposure_level")
show_rows(rows, cols)

print("\n-- Dim: generation_type × quarter --")
rows, cols, err = query("financial_performance_metrics", "generation_type, quarter",
                        ["total_revenue_usd", "net_profit_usd", "curtailment_loss_mwh"],
                        group_by="GROUP BY generation_type, quarter",
                        order_by="generation_type, quarter", limit=20)
show_rows(rows, cols, max_rows=20)


# ============================================================
# maintenance_workforce_metrics
# ============================================================
print(f"\n{'='*70}\nVALIDATING: maintenance_workforce_metrics\n{'='*70}")
maint_measures = [
    "work_order_count", "preventive_maintenance_count", "reactive_maintenance_count",
    "inspection_count", "emergency_count", "preventive_to_reactive_ratio",
    "avg_repair_duration_hours", "avg_labor_hours", "total_labor_hours",
    "total_parts_cost_usd", "completed_count", "in_progress_count",
    "assets_serviced", "technicians_active", "repeat_failure_assets",
]
print("\n-- All measures by work_order_type --")
rows, cols, err = query("maintenance_workforce_metrics", "work_order_type", maint_measures,
                        group_by="GROUP BY work_order_type", order_by="work_order_type")
show_rows(rows, cols)
report("maintenance_workforce_metrics", maint_measures, rows, err)

print("\n-- Dim: priority × status --")
rows, cols, err = query("maintenance_workforce_metrics", "priority, status",
                        ["work_order_count", "avg_repair_duration_hours", "total_parts_cost_usd"],
                        group_by="GROUP BY priority, status",
                        order_by="priority, status", limit=20)
show_rows(rows, cols, max_rows=20)

print("\n-- Dim: certification_level --")
rows, cols, err = query("maintenance_workforce_metrics", "certification_level",
                        ["work_order_count", "avg_labor_hours", "total_parts_cost_usd"],
                        group_by="GROUP BY certification_level",
                        order_by="certification_level")
show_rows(rows, cols)

print("\n-- Dim: region_name × work_order_type --")
rows, cols, err = query("maintenance_workforce_metrics", "region_name, work_order_type",
                        ["work_order_count", "total_parts_cost_usd"],
                        group_by="GROUP BY region_name, work_order_type",
                        order_by="region_name, work_order_type", limit=30)
show_rows(rows, cols, max_rows=30)

print("\n-- Dim: outage_reason (via outage_ref join) --")
rows, cols, err = query("maintenance_workforce_metrics", "outage_reason",
                        ["work_order_count", "avg_repair_duration_hours"],
                        group_by="GROUP BY outage_reason", order_by="outage_reason")
show_rows(rows, cols, max_rows=15)


# ============================================================
# executive_summary_metrics
# ============================================================
print(f"\n{'='*70}\nVALIDATING: executive_summary_metrics\n{'='*70}")
exec_measures = [
    "total_revenue_usd", "net_profit_usd", "profit_margin_pct",
    "maintenance_cost_usd", "total_generation_mwh", "avg_efficiency_pct",
    "capacity_factor_pct", "outage_count", "forced_outage_count",
    "total_downtime_hours", "total_lost_mwh", "preventive_to_reactive_ratio",
    "safety_incident_count", "lost_time_incident_count", "total_anomaly_count",
    "grid_instability_risk_score",
]
print("\n-- All measures by region_name --")
rows, cols, err = query("executive_summary_metrics", "region_name", exec_measures,
                        group_by="GROUP BY region_name", order_by="region_name")
show_rows(rows, cols)
report("executive_summary_metrics", exec_measures, rows, err)

print("\n-- Dim: regional_operational_health --")
rows, cols, err = query("executive_summary_metrics", "regional_operational_health",
                        ["outage_count", "total_revenue_usd", "avg_efficiency_pct"],
                        group_by="GROUP BY regional_operational_health",
                        order_by="regional_operational_health")
show_rows(rows, cols)

print("\n-- Dim: executive_risk_level × generation_type --")
rows, cols, err = query("executive_summary_metrics", "executive_risk_level, generation_type",
                        ["total_revenue_usd", "net_profit_usd", "forced_outage_count"],
                        group_by="GROUP BY executive_risk_level, generation_type",
                        order_by="executive_risk_level, generation_type", limit=20)
show_rows(rows, cols, max_rows=20)

print("\n-- Dim: quarter × generation_type --")
rows, cols, err = query("executive_summary_metrics", "quarter, generation_type",
                        ["total_revenue_usd", "total_generation_mwh", "safety_incident_count"],
                        group_by="GROUP BY quarter, generation_type",
                        order_by="quarter, generation_type", limit=20)
show_rows(rows, cols, max_rows=20)


# ============================================================
# FINAL SUMMARY
# ============================================================
print(f"\n{'='*70}\nFINAL RESULTS SUMMARY\n{'='*70}")
by_view = {}
for view, measure, status, val in results:
    by_view.setdefault(view, []).append((measure, status, val))

total_ok = 0
total_warn = 0
total_err = 0
for view, items in by_view.items():
    ok = sum(1 for _, s, _ in items if s == "OK")
    warn = sum(1 for _, s, _ in items if s in ("NULL", "ZERO", "EMPTY"))
    err = sum(1 for _, s, _ in items if s == "ERROR")
    total_ok += ok
    total_warn += warn
    total_err += err
    print(f"\n  {view}:  OK={ok}  WARN={warn}  ERROR={err}  (of {len(items)})")
    for m, s, v in items:
        if s != "OK":
            print(f"    [{s}] {m} = {v}")

print(f"\nTOTAL: OK={total_ok}  WARN={total_warn}  ERROR={total_err}")
spark.stop()
