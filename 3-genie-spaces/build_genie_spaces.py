"""
Build 3 Genie Spaces for the renewable energy demo:
  1. Grid Operations Intelligence       -> grid_operations_metrics
  2. Energy Financial Performance       -> financial_performance_metrics
  3. Maintenance and Workforce Ops      -> maintenance_workforce_metrics

Each space is scoped to its primary metric view plus the supporting raw tables
needed for ad-hoc questions that fall outside the curated measures.
Serialized payloads are written to /tmp; this script does NOT push them yet.
"""
from __future__ import annotations
import json
import os
import sys

sys.path.insert(0, "/Users/kailyn.klaassen/.vibe/marketplace/plugins/fe-internal-tools/skills/genie-rooms/resources")
from genie_space_builder import GenieSpaceBuilder

CATALOG = globals().get("CATALOG", "serverless_stable_cgxfyd_catalog")
SCHEMA = globals().get("SCHEMA", "kailyn_klaassen")
WAREHOUSE_ID = globals().get("WAREHOUSE_ID", "7e4da1bdd34b875f")
USER_EMAIL = globals().get("USER_EMAIL", "kailyn.klaassen@databricks.com")
PARENT_PATH = f"/Workspace/Users/{USER_EMAIL}"


def q(t):  # qualify
    return f"{CATALOG}.{SCHEMA}.{t}"


def sort_by_id_and_dump(builder: GenieSpaceBuilder, path: str) -> None:
    """Sort every id-keyed list and write as JSON. Genie requires deterministic ordering."""
    d = builder.to_dict()
    for keypath in [
        ("config", "sample_questions"),
        ("instructions", "text_instructions"),
        ("instructions", "example_question_sqls"),
        ("instructions", "sql_functions"),
        ("instructions", "join_specs"),
        ("benchmarks", "questions"),
    ]:
        node = d
        for k in keypath[:-1]:
            node = node.get(k, {}) if isinstance(node, dict) else {}
        if isinstance(node, dict) and isinstance(node.get(keypath[-1]), list):
            node[keypath[-1]].sort(key=lambda x: x.get("id", "") if isinstance(x, dict) else "")
    with open(path, "w") as f:
        json.dump(d, f, indent=2)


# ============================================================
# Space 1: Grid Operations Intelligence
# ============================================================
grid = GenieSpaceBuilder(
    title="Grid Operations Intelligence",
    description=(
        "Operational monitoring, asset health analysis, grid reliability, and renewable "
        "generation performance across utility infrastructure. Optimized for operational "
        "analytics, asset reliability, outage investigation, telemetry trend analysis, "
        "renewable generation monitoring, anomaly detection, and grid stability."
    ),
    warehouse_id=WAREHOUSE_ID,
)

grid.set_instructions("""You are a utility grid operations analyst specializing in renewable energy infrastructure, operational reliability, telemetry analysis, outage investigation, and equipment health monitoring.

Primary business users: grid operators, reliability engineers, operations leadership, site operations managers, renewable energy analysts.

PREFERRED DATA SOURCE: grid_operations_metrics (metric view). This is the curated semantic layer — use the MEASURE() function on its measures and group by its dimensions. Only drop down to the raw tables (sensor_anomalies, outages, telemetry) when the user asks a question the metric view cannot answer (e.g., event-level outage detail, specific anomaly timestamps).

QUERY PATTERN for the metric view:
  SELECT region_name, MEASURE(outage_count), MEASURE(total_downtime_hours)
  FROM grid_operations_metrics
  GROUP BY region_name

You should:
- Prioritize operational reliability and equipment health
- Explain operational degradation patterns clearly
- For outages: include likely root causes (use outage_reason), operational impact (total_downtime_hours, total_lost_mwh), and affected regions/sites
- Correlate anomalies, outages, and efficiency degradation whenever possible
- Prefer operational explanations over financial explanations
- Focus on trends, reliability, and risk identification
- Aggregate at region, site, or asset type level when appropriate
- Use business-friendly language; avoid raw telemetry jargon
- When identifying risky assets, consider anomaly_count, total_downtime_hours, avg_efficiency_pct, avg_vibration

Do not speculate beyond available metrics. If a user asks about something the curated metrics don't cover (financial impact, technician performance), redirect them to the appropriate space.""")

grid.add_metric_view(q("grid_operations_metrics"))
grid.add_table(q("sensor_anomalies"))
grid.add_table(q("outages"))
grid.add_table(q("telemetry"))
grid.add_table(q("assets"))
grid.add_table(q("sites"))
grid.add_table(q("regions"))

grid.add_example_sql(
    title="Which assets have the highest outage count and downtime this year?",
    sql=(
        "SELECT asset_tag, asset_type, region_name, "
        "MEASURE(outage_count) AS outages, "
        "MEASURE(total_downtime_hours) AS downtime_hours, "
        "MEASURE(avg_efficiency_pct) AS efficiency_pct "
        f"FROM {q('grid_operations_metrics')} "
        "GROUP BY asset_tag, asset_type, region_name "
        "ORDER BY downtime_hours DESC LIMIT 20"
    ),
)
grid.add_example_sql(
    title="Which regions are experiencing the highest grid instability?",
    sql=(
        "SELECT region_name, "
        "MEASURE(grid_instability_risk_score) AS risk_score, "
        "MEASURE(outage_count) AS outages, "
        "MEASURE(anomaly_count) AS anomalies "
        f"FROM {q('grid_operations_metrics')} "
        "GROUP BY region_name "
        "ORDER BY risk_score DESC"
    ),
)
grid.add_example_sql(
    title="Capacity factor trend by generation type over months",
    sql=(
        "SELECT month, generation_type, "
        "MEASURE(capacity_factor_pct) AS capacity_factor, "
        "MEASURE(total_power_generated_mwh) AS power_mwh "
        f"FROM {q('grid_operations_metrics')} "
        "WHERE generation_type IN ('solar','wind','battery') "
        "GROUP BY month, generation_type "
        "ORDER BY month, generation_type"
    ),
)
grid.add_example_sql(
    title="MTBF and MTTR by asset type",
    sql=(
        "SELECT asset_type, "
        "MEASURE(mtbf_hours) AS mtbf, "
        "MEASURE(mttr_hours) AS mttr, "
        "MEASURE(outage_count) AS outages "
        f"FROM {q('grid_operations_metrics')} "
        "GROUP BY asset_type ORDER BY mtbf"
    ),
)
grid.add_example_sql(
    title="Assets currently in Critical or High operational risk",
    sql=(
        "SELECT asset_tag, asset_type, site_name, region_name, "
        "operational_risk_level, asset_health_status, "
        "MEASURE(anomaly_count) AS anomalies, "
        "MEASURE(outage_count) AS outages, "
        "MEASURE(avg_efficiency_pct) AS efficiency "
        f"FROM {q('grid_operations_metrics')} "
        "WHERE operational_risk_level IN ('Critical','High') "
        "GROUP BY asset_tag, asset_type, site_name, region_name, "
        "operational_risk_level, asset_health_status "
        "ORDER BY anomalies DESC LIMIT 50"
    ),
)
grid.add_example_sql(
    title="Top outage root causes by lost generation",
    sql=(
        "SELECT outage_reason, COUNT(*) AS n_outages, "
        "ROUND(SUM(lost_generation_mwh), 0) AS total_lost_mwh, "
        "ROUND(AVG(lost_generation_mwh), 1) AS avg_lost_mwh "
        f"FROM {q('outages')} "
        "GROUP BY outage_reason ORDER BY total_lost_mwh DESC"
    ),
)

grid.validate()
sort_by_id_and_dump(grid, "/tmp/grid_serialized_space.json")
print(f"  grid space serialized -> /tmp/grid_serialized_space.json")


# ============================================================
# Space 2: Energy Financial Performance Intelligence
# ============================================================
fin = GenieSpaceBuilder(
    title="Energy Financial Performance Intelligence",
    description=(
        "Utility financial performance, market exposure, operational profitability, "
        "energy pricing, and revenue impact analysis. Optimized for profitability "
        "analysis, energy-market analytics, outage financial impact, asset financial "
        "performance, market pricing trends, and revenue optimization."
    ),
    warehouse_id=WAREHOUSE_ID,
)

fin.set_instructions("""You are a utility financial and market operations analyst specializing in renewable energy profitability, operational cost analysis, market pricing, and revenue performance.

Primary business users: finance leadership, energy trading teams, executive leadership, operations finance analysts, market analysts.

PREFERRED DATA SOURCE: financial_performance_metrics (metric view). Use MEASURE() on its measures and group by its dimensions. Drop down to power_sales, market_prices, or asset_financials only for transaction-level or hourly questions the metric view cannot answer.

QUERY PATTERN:
  SELECT region_name, MEASURE(total_revenue_usd), MEASURE(profit_margin_pct)
  FROM financial_performance_metrics
  GROUP BY region_name

You should:
- Prioritize financial outcomes and profitability
- Quantify operational events in financial terms (e.g., outage -> revenue_loss_from_outages_usd)
- For outages: include revenue impact, margin implications, regional financial exposure
- Correlate maintenance cost, outages, and profitability
- Use executive financial language
- Focus on profitability drivers, operational cost drivers, market exposure, revenue optimization
- Aggregate at region, generation_type, or site level when appropriate
- Highlight trends affecting margins or operational efficiency
- Identify financially underperforming assets or regions

Do not speculate beyond available metrics. For operational/telemetry questions redirect to Grid Operations Intelligence. For maintenance questions redirect to Maintenance and Workforce Operations Intelligence.""")

fin.add_metric_view(q("financial_performance_metrics"))
fin.add_table(q("asset_financials"))
fin.add_table(q("power_sales"))
fin.add_table(q("market_prices"))
fin.add_table(q("outages"))
fin.add_table(q("assets"))
fin.add_table(q("sites"))
fin.add_table(q("regions"))

fin.add_example_sql(
    title="Most and least profitable assets by net profit and margin",
    sql=(
        "SELECT asset_id, asset_type, site_name, region_name, "
        "MEASURE(total_revenue_usd) AS revenue, "
        "MEASURE(net_profit_usd) AS net_profit, "
        "MEASURE(profit_margin_pct) AS margin_pct "
        f"FROM {q('financial_performance_metrics')} "
        "GROUP BY asset_id, asset_type, site_name, region_name "
        "ORDER BY net_profit DESC LIMIT 20"
    ),
)
fin.add_example_sql(
    title="Regions ranked by revenue loss from outages",
    sql=(
        "SELECT region_name, market_exposure_level, "
        "MEASURE(revenue_loss_from_outages_usd) AS rev_loss, "
        "MEASURE(total_lost_mwh) AS lost_mwh, "
        "MEASURE(total_revenue_usd) AS revenue "
        f"FROM {q('financial_performance_metrics')} "
        "GROUP BY region_name, market_exposure_level "
        "ORDER BY rev_loss DESC"
    ),
)
fin.add_example_sql(
    title="Profit margin by generation type by quarter",
    sql=(
        "SELECT generation_type, quarter, "
        "MEASURE(total_revenue_usd) AS revenue, "
        "MEASURE(net_profit_usd) AS profit, "
        "MEASURE(profit_margin_pct) AS margin "
        f"FROM {q('financial_performance_metrics')} "
        "GROUP BY generation_type, quarter ORDER BY quarter, generation_type"
    ),
)
fin.add_example_sql(
    title="Hourly market price exposure by region",
    sql=(
        "SELECT r.region_name, HOUR(mp.timestamp) AS hour_of_day, "
        "ROUND(AVG(mp.real_time_price_mwh), 2) AS avg_price, "
        "ROUND(STDDEV(mp.real_time_price_mwh), 2) AS price_volatility "
        f"FROM {q('market_prices')} mp "
        f"JOIN {q('regions')} r USING(region_id) "
        "GROUP BY r.region_name, HOUR(mp.timestamp) "
        "ORDER BY r.region_name, hour_of_day"
    ),
)
fin.add_example_sql(
    title="Profitability band breakdown",
    sql=(
        "SELECT profitability_band, "
        "MEASURE(total_revenue_usd) AS revenue, "
        "MEASURE(net_profit_usd) AS net_profit, "
        "MEASURE(profit_margin_pct) AS avg_margin_pct "
        f"FROM {q('financial_performance_metrics')} "
        "GROUP BY profitability_band ORDER BY profitability_band"
    ),
)
fin.add_example_sql(
    title="Top 10 highest-cost outages by lost revenue",
    sql=(
        "SELECT o.outage_id, a.asset_type, s.site_name, r.region_name, "
        "o.outage_reason, "
        "ROUND(o.lost_generation_mwh, 1) AS lost_mwh, "
        "DATE(o.outage_start_ts) AS outage_date "
        f"FROM {q('outages')} o "
        f"JOIN {q('assets')} a USING(asset_id) "
        f"JOIN {q('sites')} s ON a.site_id = s.site_id "
        f"JOIN {q('regions')} r ON s.region_id = r.region_id "
        "ORDER BY o.lost_generation_mwh DESC LIMIT 10"
    ),
)

fin.validate()
sort_by_id_and_dump(fin, "/tmp/fin_serialized_space.json")
print(f"  financial space serialized -> /tmp/fin_serialized_space.json")


# ============================================================
# Space 3: Maintenance and Workforce Operations Intelligence
# ============================================================
maint = GenieSpaceBuilder(
    title="Maintenance and Workforce Operations Intelligence",
    description=(
        "Maintenance execution, workforce operations, outage response, asset servicing, "
        "operational readiness, and safety performance. Optimized for maintenance "
        "analytics, workforce utilization, outage response, maintenance backlog, "
        "technician performance, preventive maintenance effectiveness, and safety/compliance."
    ),
    warehouse_id=WAREHOUSE_ID,
)

maint.set_instructions("""You are a utility maintenance and workforce operations analyst specializing in maintenance execution, workforce planning, outage response, and operational readiness.

Primary business users: maintenance leadership, field operations managers, workforce planners, reliability operations teams, safety and compliance leadership.

PREFERRED DATA SOURCE: maintenance_workforce_metrics (metric view) for work-order-level analytics. Use the raw tables for questions outside the metric view's scope:
- safety_incidents — for safety incident counts/severity (the metric view doesn't expose these)
- maintenance_schedule — for overdue items and scheduling
- assets, technicians, sites, regions — for dim lookups

QUERY PATTERN:
  SELECT work_order_type, MEASURE(work_order_count), MEASURE(avg_repair_duration_hours)
  FROM maintenance_workforce_metrics
  GROUP BY work_order_type

You should:
- Prioritize maintenance effectiveness and operational readiness
- Correlate maintenance behavior with asset reliability whenever possible
- For outages: include response effectiveness, maintenance workload, workforce implications
- Focus on preventive maintenance, workforce efficiency, maintenance backlog, repair effectiveness, operational response
- Use operational-leadership language over engineering jargon
- Aggregate at region, site, or asset_type level
- Identify maintenance bottlenecks and workforce strain
- Highlight repeat failure patterns and maintenance inefficiencies
- Explain operational consequences of delayed maintenance

For safety questions, query the safety_incidents table directly (it isn't part of the curated metric view). For overdue maintenance counts, query maintenance_schedule directly.

Do not speculate beyond available data.""")

maint.add_metric_view(q("maintenance_workforce_metrics"))
maint.add_table(q("work_orders"))
maint.add_table(q("maintenance_schedule"))
maint.add_table(q("safety_incidents"))
maint.add_table(q("technicians"))
maint.add_table(q("outages"))
maint.add_table(q("assets"))
maint.add_table(q("sites"))
maint.add_table(q("regions"))

maint.add_example_sql(
    title="Preventive vs reactive maintenance ratio by region",
    sql=(
        "SELECT region_name, "
        "MEASURE(preventive_maintenance_count) AS preventive, "
        "MEASURE(reactive_maintenance_count) AS reactive, "
        "MEASURE(preventive_to_reactive_ratio) AS ratio, "
        "MEASURE(emergency_count) AS emergency "
        f"FROM {q('maintenance_workforce_metrics')} "
        "GROUP BY region_name ORDER BY ratio"
    ),
)
maint.add_example_sql(
    title="Technician workload — work orders, labor hours, parts cost",
    sql=(
        "SELECT technician_name, certification_level, region_name, "
        "MEASURE(work_order_count) AS wo_count, "
        "MEASURE(total_labor_hours) AS labor_hrs, "
        "MEASURE(total_parts_cost_usd) AS parts_cost "
        f"FROM {q('maintenance_workforce_metrics')} "
        "GROUP BY technician_name, certification_level, region_name "
        "ORDER BY wo_count DESC LIMIT 30"
    ),
)
maint.add_example_sql(
    title="Assets with repeat failures (multiple reactive/emergency WOs)",
    sql=(
        "SELECT a.asset_id, a.asset_tag, a.asset_type, s.site_name, r.region_name, "
        "COUNT(*) AS reactive_emergency_wos "
        f"FROM {q('work_orders')} wo "
        f"JOIN {q('assets')} a ON wo.asset_id = a.asset_id "
        f"JOIN {q('sites')} s ON a.site_id = s.site_id "
        f"JOIN {q('regions')} r ON s.region_id = r.region_id "
        "WHERE wo.work_order_type IN ('reactive','emergency') "
        "GROUP BY a.asset_id, a.asset_tag, a.asset_type, s.site_name, r.region_name "
        "HAVING COUNT(*) >= 3 "
        "ORDER BY reactive_emergency_wos DESC LIMIT 30"
    ),
)
maint.add_example_sql(
    title="Maintenance backlog — overdue items by asset type and region",
    sql=(
        "SELECT a.asset_type, r.region_name, "
        "COUNT(*) FILTER (WHERE ms.overdue_flag) AS overdue_count, "
        "COUNT(*) AS total_scheduled, "
        "ROUND(100.0 * COUNT(*) FILTER (WHERE ms.overdue_flag) / COUNT(*), 1) AS overdue_pct "
        f"FROM {q('maintenance_schedule')} ms "
        f"JOIN {q('assets')} a USING(asset_id) "
        f"JOIN {q('sites')} s ON a.site_id = s.site_id "
        f"JOIN {q('regions')} r ON s.region_id = r.region_id "
        "GROUP BY a.asset_type, r.region_name "
        "ORDER BY overdue_pct DESC"
    ),
)
maint.add_example_sql(
    title="Safety incidents by severity and region",
    sql=(
        "SELECT r.region_name, si.severity, "
        "COUNT(*) AS incident_count, "
        "SUM(CASE WHEN si.lost_time_flag THEN 1 ELSE 0 END) AS lost_time_incidents "
        f"FROM {q('safety_incidents')} si "
        f"JOIN {q('sites')} s ON si.site_id = s.site_id "
        f"JOIN {q('regions')} r ON s.region_id = r.region_id "
        "GROUP BY r.region_name, si.severity "
        "ORDER BY r.region_name, si.severity"
    ),
)
maint.add_example_sql(
    title="Avg repair duration by priority and outage reason",
    sql=(
        "SELECT priority, outage_reason, "
        "MEASURE(work_order_count) AS wo_count, "
        "MEASURE(avg_repair_duration_hours) AS avg_repair_hrs, "
        "MEASURE(avg_labor_hours) AS avg_labor_hrs "
        f"FROM {q('maintenance_workforce_metrics')} "
        "WHERE outage_reason IS NOT NULL "
        "GROUP BY priority, outage_reason "
        "ORDER BY avg_repair_hrs DESC"
    ),
)

maint.validate()
sort_by_id_and_dump(maint, "/tmp/maint_serialized_space.json")
print(f"  maintenance space serialized -> /tmp/maint_serialized_space.json")


# ============================================================
# Build outer create-space request payloads
# ============================================================
def make_create_payload(builder: GenieSpaceBuilder, serialized_path: str, out_path: str):
    with open(serialized_path) as f:
        serialized = f.read()
    payload = {
        "title": builder.title,
        "description": builder.description,
        "parent_path": PARENT_PATH,
        "warehouse_id": builder.warehouse_id,
        "serialized_space": serialized,
    }
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)


make_create_payload(grid, "/tmp/grid_serialized_space.json", "/tmp/grid_create.json")
make_create_payload(fin, "/tmp/fin_serialized_space.json", "/tmp/fin_create.json")
make_create_payload(maint, "/tmp/maint_serialized_space.json", "/tmp/maint_create.json")

print("\nCreate-space payloads ready:")
print("  /tmp/grid_create.json")
print("  /tmp/fin_create.json")
print("  /tmp/maint_create.json")
