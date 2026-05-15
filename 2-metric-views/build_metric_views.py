"""
Build rollup tables + 4 Metric Views for the renewable energy demo.

Layer architecture:
  asset_daily_summary (~237k rows)  ── grid_operations_metrics
                                   └─ financial_performance_metrics
  region_daily_summary (~8.7k rows) ─── executive_summary_metrics
  work_orders (raw, ~6k rows)       ─── maintenance_workforce_metrics
"""

import os
from databricks.connect import DatabricksSession

CAT = "serverless_stable_cgxfyd_catalog"
SCH = "kailyn_klaassen"
PROFILE = "fe-vm-serverless-stable-cgxfyd"
os.environ["DATABRICKS_CONFIG_PROFILE"] = PROFILE

spark = DatabricksSession.builder.profile(PROFILE).serverless().getOrCreate()
spark.sql(f"USE {CAT}.{SCH}")
print(f"Connected to {CAT}.{SCH}\n")


def step(label):
    print(f"\n=== {label} ===")


def run_sql(sql, label=None):
    if label:
        print(f"  {label}")
    spark.sql(sql)


# ============================================================
# ROLLUP 1: asset_daily_summary
# ============================================================
step("Build asset_daily_summary")

# Pre-compute per-asset capacity slice (site capacity / assets-at-site)
run_sql(f"""
CREATE OR REPLACE TEMPORARY VIEW _asset_cap AS
SELECT a.asset_id,
       a.site_id,
       s.capacity_mw / NULLIF(COUNT(*) OVER (PARTITION BY a.site_id), 0) AS asset_capacity_mw,
       a.asset_type IN ('wind_turbine','inverter','battery_unit') AS is_generation_asset
FROM {CAT}.{SCH}.assets a
JOIN {CAT}.{SCH}.sites s ON a.site_id = s.site_id
""", "asset capacity slice")

run_sql(f"""
CREATE OR REPLACE TEMPORARY VIEW _telemetry_daily AS
SELECT
  asset_id,
  DATE(timestamp) AS date,
  AVG(temperature) AS avg_temperature,
  MAX(temperature) AS max_temperature,
  AVG(vibration) AS avg_vibration,
  MAX(vibration) AS max_vibration,
  AVG(efficiency_pct) AS avg_efficiency_pct,
  AVG(power_output_mw) * 24.0 AS total_power_mwh,
  SUM(CASE WHEN alarm_flag THEN 1 ELSE 0 END) AS alarm_count,
  STDDEV(voltage) AS voltage_stddev,
  TRUE AS has_telemetry
FROM {CAT}.{SCH}.telemetry
GROUP BY asset_id, DATE(timestamp)
""", "telemetry daily aggregates")

run_sql(f"""
CREATE OR REPLACE TEMPORARY VIEW _anomalies_daily AS
SELECT asset_id, DATE(timestamp) AS date,
       COUNT(*) AS anomaly_count,
       MAX(severity_score) AS max_severity_score
FROM {CAT}.{SCH}.sensor_anomalies
GROUP BY asset_id, DATE(timestamp)
""", "anomaly daily counts")

run_sql(f"""
CREATE OR REPLACE TEMPORARY VIEW _outages_daily AS
SELECT
  asset_id, DATE(outage_start_ts) AS date,
  COUNT(DISTINCT outage_id) AS outage_count,
  COUNT(DISTINCT CASE WHEN forced_outage_flag THEN outage_id END) AS forced_outage_count,
  SUM((UNIX_TIMESTAMP(outage_end_ts) - UNIX_TIMESTAMP(outage_start_ts))/3600.0) AS total_downtime_hours,
  SUM(lost_generation_mwh) AS total_lost_mwh
FROM {CAT}.{SCH}.outages
GROUP BY asset_id, DATE(outage_start_ts)
""", "outage daily aggregates (attributed to start date)")

run_sql(f"""
CREATE OR REPLACE TEMPORARY VIEW _work_orders_daily AS
SELECT
  asset_id, DATE(created_ts) AS date,
  COUNT(*) AS work_order_count,
  SUM(CASE WHEN work_order_type='emergency' THEN 1 ELSE 0 END) AS emergency_wo_count,
  SUM(CASE WHEN work_order_type='reactive' THEN 1 ELSE 0 END) AS reactive_wo_count,
  SUM(CASE WHEN work_order_type='preventive' THEN 1 ELSE 0 END) AS preventive_wo_count,
  SUM(CASE WHEN work_order_type='inspection' THEN 1 ELSE 0 END) AS inspection_wo_count,
  SUM(labor_hours) AS total_labor_hours,
  SUM(parts_cost_usd) AS total_parts_cost
FROM {CAT}.{SCH}.work_orders
GROUP BY asset_id, DATE(created_ts)
""", "work order daily aggregates")

run_sql(f"""
CREATE OR REPLACE TEMPORARY VIEW _maintenance_daily AS
SELECT asset_id, planned_date AS date,
       COUNT(CASE WHEN overdue_flag THEN 1 END) AS overdue_maintenance_count,
       COUNT(*) AS scheduled_count
FROM {CAT}.{SCH}.maintenance_schedule
GROUP BY asset_id, planned_date
""", "maintenance schedule daily counts")

run_sql(f"""
CREATE OR REPLACE TABLE {CAT}.{SCH}.asset_daily_summary AS
SELECT
  af.asset_id,
  af.date,
  ac.asset_capacity_mw,
  ac.is_generation_asset,
  CASE WHEN td.has_telemetry AND ac.is_generation_asset
       THEN ac.asset_capacity_mw * 24.0 END AS theoretical_max_daily_mwh,

  -- Financials
  af.revenue_usd,
  af.opex_usd,
  af.maintenance_cost_usd AS finance_maintenance_cost_usd,
  af.curtailed_mwh,
  af.revenue_usd - af.opex_usd - af.maintenance_cost_usd AS net_profit_usd,
  af.profit_margin_pct,

  -- Telemetry
  td.avg_temperature, td.max_temperature,
  td.avg_vibration, td.max_vibration,
  td.avg_efficiency_pct,
  td.total_power_mwh,
  td.alarm_count,
  td.voltage_stddev,
  COALESCE(td.has_telemetry, FALSE) AS has_telemetry,

  -- Anomalies
  COALESCE(ad.anomaly_count, 0) AS anomaly_count,
  ad.max_severity_score,

  -- Outages
  COALESCE(od.outage_count, 0) AS outage_count,
  COALESCE(od.forced_outage_count, 0) AS forced_outage_count,
  COALESCE(od.total_downtime_hours, 0.0) AS total_downtime_hours,
  COALESCE(od.total_lost_mwh, 0.0) AS total_lost_mwh,

  -- Work orders
  COALESCE(wd.work_order_count, 0) AS work_order_count,
  COALESCE(wd.emergency_wo_count, 0) AS emergency_wo_count,
  COALESCE(wd.reactive_wo_count, 0) AS reactive_wo_count,
  COALESCE(wd.preventive_wo_count, 0) AS preventive_wo_count,
  COALESCE(wd.inspection_wo_count, 0) AS inspection_wo_count,
  COALESCE(wd.total_labor_hours, 0.0) AS total_labor_hours,
  COALESCE(wd.total_parts_cost, 0.0) AS wo_total_parts_cost,

  -- Maintenance schedule
  COALESCE(md.overdue_maintenance_count, 0) AS overdue_maintenance_count,
  COALESCE(md.scheduled_count, 0) AS scheduled_count
FROM {CAT}.{SCH}.asset_financials af
JOIN _asset_cap ac ON af.asset_id = ac.asset_id
LEFT JOIN _telemetry_daily td ON af.asset_id = td.asset_id AND af.date = td.date
LEFT JOIN _anomalies_daily ad ON af.asset_id = ad.asset_id AND af.date = ad.date
LEFT JOIN _outages_daily od ON af.asset_id = od.asset_id AND af.date = od.date
LEFT JOIN _work_orders_daily wd ON af.asset_id = wd.asset_id AND af.date = wd.date
LEFT JOIN _maintenance_daily md ON af.asset_id = md.asset_id AND af.date = md.date
""", "writing asset_daily_summary")

n = spark.table(f"{CAT}.{SCH}.asset_daily_summary").count()
print(f"  asset_daily_summary: {n:,} rows")


# ============================================================
# ROLLUP 2: region_daily_summary
# ============================================================
step("Build region_daily_summary")

run_sql(f"""
CREATE OR REPLACE TEMPORARY VIEW _safety_daily_region AS
SELECT s.region_id, DATE(si.incident_ts) AS date,
       COUNT(*) AS safety_incident_count,
       SUM(CASE WHEN si.lost_time_flag THEN 1 ELSE 0 END) AS lost_time_incident_count
FROM {CAT}.{SCH}.safety_incidents si
JOIN {CAT}.{SCH}.sites s ON si.site_id = s.site_id
GROUP BY s.region_id, DATE(si.incident_ts)
""", "safety incidents daily by region")

run_sql(f"""
CREATE OR REPLACE TABLE {CAT}.{SCH}.region_daily_summary AS
WITH base AS (
  SELECT
    s.region_id, r.region_name, s.generation_type, ads.date,
    ads.revenue_usd, ads.opex_usd, ads.finance_maintenance_cost_usd,
    ads.curtailed_mwh, ads.net_profit_usd, ads.profit_margin_pct,
    ads.total_power_mwh, ads.theoretical_max_daily_mwh,
    ads.avg_efficiency_pct, ads.has_telemetry,
    ads.anomaly_count, ads.outage_count, ads.forced_outage_count,
    ads.total_downtime_hours, ads.total_lost_mwh,
    ads.work_order_count, ads.emergency_wo_count, ads.reactive_wo_count,
    ads.preventive_wo_count, ads.inspection_wo_count,
    ads.total_labor_hours, ads.wo_total_parts_cost,
    ads.overdue_maintenance_count,
    ads.alarm_count
  FROM {CAT}.{SCH}.asset_daily_summary ads
  JOIN {CAT}.{SCH}.assets a ON ads.asset_id = a.asset_id
  JOIN {CAT}.{SCH}.sites s ON a.site_id = s.site_id
  JOIN {CAT}.{SCH}.regions r ON s.region_id = r.region_id
)
SELECT
  b.region_id, b.region_name, b.generation_type, b.date,
  SUM(b.revenue_usd) AS total_revenue_usd,
  SUM(b.opex_usd) AS total_opex_usd,
  SUM(b.finance_maintenance_cost_usd) AS total_maintenance_cost_usd,
  SUM(b.curtailed_mwh) AS total_curtailed_mwh,
  SUM(b.net_profit_usd) AS net_profit_usd,
  AVG(b.profit_margin_pct) AS avg_profit_margin_pct,
  SUM(b.total_power_mwh) AS total_power_mwh,
  SUM(b.theoretical_max_daily_mwh) AS total_theoretical_max_mwh,
  AVG(b.avg_efficiency_pct) AS avg_efficiency_pct,
  SUM(b.anomaly_count) AS total_anomaly_count,
  SUM(b.outage_count) AS total_outage_count,
  SUM(b.forced_outage_count) AS total_forced_outage_count,
  SUM(b.total_downtime_hours) AS total_downtime_hours,
  SUM(b.total_lost_mwh) AS total_lost_mwh,
  SUM(b.work_order_count) AS total_work_order_count,
  SUM(b.emergency_wo_count) AS total_emergency_wo_count,
  SUM(b.reactive_wo_count) AS total_reactive_wo_count,
  SUM(b.preventive_wo_count) AS total_preventive_wo_count,
  SUM(b.inspection_wo_count) AS total_inspection_wo_count,
  SUM(b.total_labor_hours) AS total_labor_hours,
  SUM(b.wo_total_parts_cost) AS total_parts_cost,
  SUM(b.overdue_maintenance_count) AS total_overdue_maintenance_count,
  SUM(b.alarm_count) AS total_alarm_count,
  COALESCE(sd.safety_incident_count, 0) AS safety_incident_count,
  COALESCE(sd.lost_time_incident_count, 0) AS lost_time_incident_count
FROM base b
LEFT JOIN _safety_daily_region sd ON b.region_id = sd.region_id AND b.date = sd.date
GROUP BY b.region_id, b.region_name, b.generation_type, b.date,
         sd.safety_incident_count, sd.lost_time_incident_count
""", "writing region_daily_summary")

n = spark.table(f"{CAT}.{SCH}.region_daily_summary").count()
print(f"  region_daily_summary: {n:,} rows")


# ============================================================
# METRIC VIEW 1: grid_operations_metrics
# ============================================================
step("Create grid_operations_metrics")

GRID_OPS_YAML = f"""
version: 1.1
comment: "Grid operations and reliability KPIs at asset-day grain. Joins to assets/sites/regions."
source: {CAT}.{SCH}.asset_daily_summary

joins:
  - name: asset
    source: {CAT}.{SCH}.assets
    on: source.asset_id = asset.asset_id
    joins:
      - name: site
        source: {CAT}.{SCH}.sites
        on: asset.site_id = site.site_id
        joins:
          - name: region
            source: {CAT}.{SCH}.regions
            on: site.region_id = region.region_id

dimensions:
  - name: asset_id
    expr: source.asset_id
    display_name: "Asset ID"
  - name: asset_tag
    expr: asset.asset_tag
    display_name: "Asset Tag"
  - name: asset_type
    expr: asset.asset_type
    display_name: "Asset Type"
  - name: manufacturer
    expr: asset.manufacturer
    display_name: "Manufacturer"
  - name: site_name
    expr: asset.site.site_name
    display_name: "Site"
  - name: generation_type
    expr: asset.site.generation_type
    display_name: "Generation Type"
  - name: region_name
    expr: asset.site.region.region_name
    display_name: "Region"
  - name: date
    expr: source.date
    display_name: "Date"
  - name: month
    expr: "DATE_TRUNC('MONTH', source.date)"
    display_name: "Month"
  - name: quarter
    expr: "DATE_TRUNC('QUARTER', source.date)"
    display_name: "Quarter"
  - name: year
    expr: "YEAR(source.date)"
    display_name: "Year"
  - name: asset_health_status
    expr: |-
      CASE
        WHEN source.forced_outage_count > 0 AND source.anomaly_count >= 2 THEN 'Critical'
        WHEN source.avg_efficiency_pct IS NOT NULL AND source.avg_efficiency_pct < 80 THEN 'Degrading'
        WHEN source.anomaly_count > 0 OR source.alarm_count > 10 THEN 'Watchlist'
        ELSE 'Healthy'
      END
    display_name: "Asset Health Status"
  - name: operational_risk_level
    expr: |-
      CASE
        WHEN source.forced_outage_count > 0 AND source.anomaly_count >= 5 THEN 'Critical'
        WHEN source.anomaly_count >= 2 OR source.alarm_count > 50 THEN 'High'
        WHEN source.anomaly_count >= 1 OR source.alarm_count > 10 THEN 'Medium'
        ELSE 'Low'
      END
    display_name: "Operational Risk Level"

measures:
  - name: avg_temperature
    expr: AVG(source.avg_temperature)
    display_name: "Avg Temperature (°C)"
  - name: max_temperature
    expr: MAX(source.max_temperature)
    display_name: "Max Temperature (°C)"
  - name: avg_vibration
    expr: AVG(source.avg_vibration)
    display_name: "Avg Vibration"
  - name: avg_efficiency_pct
    expr: AVG(source.avg_efficiency_pct)
    display_name: "Avg Efficiency (%)"
  - name: total_power_generated_mwh
    expr: SUM(source.total_power_mwh)
    display_name: "Total Energy Generated (MWh)"
  - name: anomaly_count
    expr: SUM(source.anomaly_count)
    display_name: "Anomaly Count"
  - name: outage_count
    expr: SUM(source.outage_count)
    display_name: "Outage Count"
  - name: forced_outage_count
    expr: SUM(source.forced_outage_count)
    display_name: "Forced Outage Count"
  - name: total_downtime_hours
    expr: SUM(source.total_downtime_hours)
    display_name: "Total Downtime (hrs)"
  - name: mttr_hours
    expr: SUM(source.total_downtime_hours) / NULLIF(SUM(source.outage_count), 0)
    display_name: "MTTR (hrs)"
  - name: mtbf_hours
    expr: (8760.0 * COUNT(DISTINCT source.asset_id)) / NULLIF(SUM(source.outage_count), 0)
    display_name: "MTBF (hrs)"
  - name: capacity_factor_pct
    expr: 100.0 * SUM(source.total_power_mwh) / NULLIF(SUM(source.theoretical_max_daily_mwh), 0)
    display_name: "Capacity Factor (%)"
  - name: alarm_count
    expr: SUM(source.alarm_count)
    display_name: "Alarm Count"
  - name: overdue_maintenance_count
    expr: SUM(source.overdue_maintenance_count)
    display_name: "Overdue Maintenance Count"
  - name: grid_instability_risk_score
    expr: |-
      100.0 * (
        0.30 * COALESCE(AVG(source.voltage_stddev), 0) / 20.0 +
        0.30 * COALESCE(AVG(source.avg_vibration), 0) / 5.0 +
        0.20 * COALESCE(AVG(source.max_severity_score), 0) / 10.0 +
        0.20 * LEAST(1.0, SUM(source.forced_outage_count) / GREATEST(COUNT(DISTINCT source.asset_id), 1) / 5.0)
      )
    display_name: "Grid Instability Risk Score"
"""

spark.sql(f"""
CREATE OR REPLACE VIEW {CAT}.{SCH}.grid_operations_metrics
WITH METRICS LANGUAGE YAML AS $${GRID_OPS_YAML}$$
""")
print("  grid_operations_metrics created")


# ============================================================
# METRIC VIEW 2: financial_performance_metrics
# ============================================================
step("Create financial_performance_metrics")

FIN_YAML = f"""
version: 1.1
comment: "Financial performance and market-exposure KPIs at asset-day grain."
source: {CAT}.{SCH}.asset_daily_summary

joins:
  - name: asset
    source: {CAT}.{SCH}.assets
    on: source.asset_id = asset.asset_id
    joins:
      - name: site
        source: {CAT}.{SCH}.sites
        on: asset.site_id = site.site_id
        joins:
          - name: region
            source: {CAT}.{SCH}.regions
            on: site.region_id = region.region_id

dimensions:
  - name: asset_id
    expr: source.asset_id
    display_name: "Asset ID"
  - name: asset_type
    expr: asset.asset_type
    display_name: "Asset Type"
  - name: site_name
    expr: asset.site.site_name
    display_name: "Site"
  - name: generation_type
    expr: asset.site.generation_type
    display_name: "Generation Type"
  - name: region_name
    expr: asset.site.region.region_name
    display_name: "Market Region"
  - name: date
    expr: source.date
    display_name: "Date"
  - name: month
    expr: "DATE_TRUNC('MONTH', source.date)"
    display_name: "Month"
  - name: quarter
    expr: "DATE_TRUNC('QUARTER', source.date)"
    display_name: "Quarter"
  - name: year
    expr: "YEAR(source.date)"
    display_name: "Year"
  - name: profitability_band
    expr: |-
      CASE
        WHEN source.profit_margin_pct < 0 THEN 'Negative'
        WHEN source.profit_margin_pct < 10 THEN 'Low Margin'
        WHEN source.profit_margin_pct < 30 THEN 'Moderate Margin'
        ELSE 'High Margin'
      END
    display_name: "Profitability Band"
  - name: market_exposure_level
    expr: |-
      CASE asset.site.region.region_name
        WHEN 'CAISO' THEN 'High'
        WHEN 'ERCOT' THEN 'High'
        WHEN 'NYISO' THEN 'High'
        WHEN 'PJM' THEN 'Medium'
        WHEN 'SE-Reliability' THEN 'Medium'
        ELSE 'Low'
      END
    display_name: "Market Exposure Level"
  - name: forced_outage_flag
    expr: source.forced_outage_count > 0
    display_name: "Had Forced Outage"

measures:
  - name: total_revenue_usd
    expr: SUM(source.revenue_usd)
    display_name: "Total Revenue (USD)"
  - name: total_opex_usd
    expr: SUM(source.opex_usd)
    display_name: "Total OpEx (USD)"
  - name: total_maintenance_cost_usd
    expr: SUM(source.finance_maintenance_cost_usd)
    display_name: "Total Maintenance Cost (USD)"
  - name: net_profit_usd
    expr: SUM(source.net_profit_usd)
    display_name: "Net Profit (USD)"
  - name: profit_margin_pct
    expr: 100.0 * SUM(source.net_profit_usd) / NULLIF(SUM(source.revenue_usd), 0)
    display_name: "Profit Margin (%)"
  - name: revenue_loss_from_outages_usd
    expr: |-
      SUM(source.total_lost_mwh) *
      (SUM(source.revenue_usd) / NULLIF(SUM(source.total_power_mwh), 0))
    display_name: "Revenue Loss From Outages (USD)"
  - name: curtailment_loss_mwh
    expr: SUM(source.curtailed_mwh)
    display_name: "Curtailment Loss (MWh)"
  - name: revenue_per_mwh
    expr: SUM(source.revenue_usd) / NULLIF(SUM(source.total_power_mwh), 0)
    display_name: "Revenue per MWh ($/MWh)"
  - name: total_lost_mwh
    expr: SUM(source.total_lost_mwh)
    display_name: "Total Lost Generation (MWh)"
"""

spark.sql(f"""
CREATE OR REPLACE VIEW {CAT}.{SCH}.financial_performance_metrics
WITH METRICS LANGUAGE YAML AS $${FIN_YAML}$$
""")
print("  financial_performance_metrics created")


# ============================================================
# METRIC VIEW 3: maintenance_workforce_metrics
# ============================================================
step("Create maintenance_workforce_metrics")

MAINT_YAML = f"""
version: 1.1
comment: "Maintenance execution and workforce KPIs at work-order grain."
source: {CAT}.{SCH}.work_orders

joins:
  - name: asset
    source: {CAT}.{SCH}.assets
    on: source.asset_id = asset.asset_id
    joins:
      - name: site
        source: {CAT}.{SCH}.sites
        on: asset.site_id = site.site_id
        joins:
          - name: region
            source: {CAT}.{SCH}.regions
            on: site.region_id = region.region_id
  - name: technician
    source: {CAT}.{SCH}.technicians
    on: source.technician_id = technician.technician_id
  - name: outage_ref
    source: {CAT}.{SCH}.outages
    on: source.outage_id = outage_ref.outage_id

dimensions:
  - name: technician_id
    expr: source.technician_id
    display_name: "Technician ID"
  - name: technician_name
    expr: technician.technician_name
    display_name: "Technician"
  - name: certification_level
    expr: technician.certification_level
    display_name: "Certification Level"
  - name: asset_id
    expr: source.asset_id
    display_name: "Asset ID"
  - name: asset_type
    expr: asset.asset_type
    display_name: "Asset Type"
  - name: site_name
    expr: asset.site.site_name
    display_name: "Site"
  - name: region_name
    expr: asset.site.region.region_name
    display_name: "Region"
  - name: work_order_type
    expr: source.work_order_type
    display_name: "Work Order Type"
  - name: priority
    expr: source.priority
    display_name: "Priority"
  - name: status
    expr: source.status
    display_name: "Status"
  - name: created_date
    expr: DATE(source.created_ts)
    display_name: "Created Date"
  - name: created_month
    expr: "DATE_TRUNC('MONTH', source.created_ts)"
    display_name: "Created Month"
  - name: outage_reason
    expr: outage_ref.outage_reason
    display_name: "Outage Reason"
  - name: forced_outage_flag
    expr: outage_ref.forced_outage_flag
    display_name: "Forced Outage"

measures:
  - name: work_order_count
    expr: COUNT(source.work_order_id)
    display_name: "Work Order Count"
  - name: preventive_maintenance_count
    expr: SUM(CASE WHEN source.work_order_type='preventive' THEN 1 ELSE 0 END)
    display_name: "Preventive Maintenance Count"
  - name: reactive_maintenance_count
    expr: SUM(CASE WHEN source.work_order_type IN ('reactive','emergency') THEN 1 ELSE 0 END)
    display_name: "Reactive Maintenance Count"
  - name: inspection_count
    expr: SUM(CASE WHEN source.work_order_type='inspection' THEN 1 ELSE 0 END)
    display_name: "Inspection Count"
  - name: emergency_count
    expr: SUM(CASE WHEN source.work_order_type='emergency' THEN 1 ELSE 0 END)
    display_name: "Emergency Count"
  - name: preventive_to_reactive_ratio
    expr: |-
      SUM(CASE WHEN source.work_order_type='preventive' THEN 1 ELSE 0 END) /
      NULLIF(SUM(CASE WHEN source.work_order_type IN ('reactive','emergency') THEN 1 ELSE 0 END), 0)
    display_name: "Preventive : Reactive Ratio"
  - name: avg_repair_duration_hours
    expr: AVG((UNIX_TIMESTAMP(source.completed_ts) - UNIX_TIMESTAMP(source.created_ts)) / 3600.0)
    display_name: "Avg Repair Duration (hrs)"
  - name: avg_labor_hours
    expr: AVG(source.labor_hours)
    display_name: "Avg Labor Hours"
  - name: total_labor_hours
    expr: SUM(source.labor_hours)
    display_name: "Total Labor Hours"
  - name: total_parts_cost_usd
    expr: SUM(source.parts_cost_usd)
    display_name: "Total Parts Cost (USD)"
  - name: completed_count
    expr: SUM(CASE WHEN source.status='completed' THEN 1 ELSE 0 END)
    display_name: "Completed Count"
  - name: in_progress_count
    expr: SUM(CASE WHEN source.status='in_progress' THEN 1 ELSE 0 END)
    display_name: "In Progress Count"
  - name: assets_serviced
    expr: COUNT(DISTINCT source.asset_id)
    display_name: "Assets Serviced"
  - name: technicians_active
    expr: COUNT(DISTINCT source.technician_id)
    display_name: "Active Technicians"
  - name: repeat_failure_assets
    expr: COUNT(DISTINCT CASE WHEN source.work_order_type IN ('reactive','emergency') THEN source.asset_id END)
    display_name: "Assets With Repeat Failures"
"""

spark.sql(f"""
CREATE OR REPLACE VIEW {CAT}.{SCH}.maintenance_workforce_metrics
WITH METRICS LANGUAGE YAML AS $${MAINT_YAML}$$
""")
print("  maintenance_workforce_metrics created")


# ============================================================
# METRIC VIEW 4: executive_summary_metrics
# ============================================================
step("Create executive_summary_metrics")

EXEC_YAML = f"""
version: 1.1
comment: "Executive rollup at region × generation_type × date grain. Single semantic layer for leadership Q&A."
source: {CAT}.{SCH}.region_daily_summary

dimensions:
  - name: region_name
    expr: source.region_name
    display_name: "Region"
  - name: generation_type
    expr: source.generation_type
    display_name: "Generation Type"
  - name: date
    expr: source.date
    display_name: "Date"
  - name: month
    expr: "DATE_TRUNC('MONTH', source.date)"
    display_name: "Month"
  - name: quarter
    expr: "DATE_TRUNC('QUARTER', source.date)"
    display_name: "Quarter"
  - name: year
    expr: "YEAR(source.date)"
    display_name: "Year"
  - name: profitability_band
    expr: |-
      CASE
        WHEN source.avg_profit_margin_pct < 0 THEN 'Negative'
        WHEN source.avg_profit_margin_pct < 10 THEN 'Low Margin'
        WHEN source.avg_profit_margin_pct < 30 THEN 'Moderate Margin'
        ELSE 'High Margin'
      END
    display_name: "Profitability Band"
  - name: regional_operational_health
    expr: |-
      CASE
        WHEN source.total_forced_outage_count > 5 OR source.avg_efficiency_pct < 75 THEN 'Critical'
        WHEN source.total_forced_outage_count > 2 OR source.avg_efficiency_pct < 85 THEN 'Stressed'
        WHEN source.total_forced_outage_count > 0 THEN 'Watch'
        ELSE 'Healthy'
      END
    display_name: "Regional Operational Health"
  - name: executive_risk_level
    expr: |-
      CASE
        WHEN source.total_forced_outage_count > 3 AND source.avg_profit_margin_pct < 0 THEN 'Critical'
        WHEN source.total_forced_outage_count > 1 OR source.avg_profit_margin_pct < 10 THEN 'High'
        WHEN source.total_anomaly_count > 5 OR source.total_overdue_maintenance_count > 2 THEN 'Medium'
        ELSE 'Low'
      END
    display_name: "Executive Risk Level"

measures:
  - name: total_revenue_usd
    expr: SUM(source.total_revenue_usd)
    display_name: "Total Revenue (USD)"
  - name: net_profit_usd
    expr: SUM(source.net_profit_usd)
    display_name: "Net Profit (USD)"
  - name: profit_margin_pct
    expr: 100.0 * SUM(source.net_profit_usd) / NULLIF(SUM(source.total_revenue_usd), 0)
    display_name: "Profit Margin (%)"
  - name: maintenance_cost_usd
    expr: SUM(source.total_maintenance_cost_usd)
    display_name: "Maintenance Cost (USD)"
  - name: total_generation_mwh
    expr: SUM(source.total_power_mwh)
    display_name: "Total Generation (MWh)"
  - name: avg_efficiency_pct
    expr: AVG(source.avg_efficiency_pct)
    display_name: "Avg Efficiency (%)"
  - name: capacity_factor_pct
    expr: 100.0 * SUM(source.total_power_mwh) / NULLIF(SUM(source.total_theoretical_max_mwh), 0)
    display_name: "Capacity Factor (%)"
  - name: outage_count
    expr: SUM(source.total_outage_count)
    display_name: "Outage Count"
  - name: forced_outage_count
    expr: SUM(source.total_forced_outage_count)
    display_name: "Forced Outage Count"
  - name: total_downtime_hours
    expr: SUM(source.total_downtime_hours)
    display_name: "Total Downtime (hrs)"
  - name: total_lost_mwh
    expr: SUM(source.total_lost_mwh)
    display_name: "Total Lost Generation (MWh)"
  - name: preventive_to_reactive_ratio
    expr: |-
      SUM(source.total_preventive_wo_count) /
      NULLIF(SUM(source.total_reactive_wo_count) + SUM(source.total_emergency_wo_count), 0)
    display_name: "Preventive : Reactive Ratio"
  - name: safety_incident_count
    expr: SUM(source.safety_incident_count)
    display_name: "Safety Incident Count"
  - name: lost_time_incident_count
    expr: SUM(source.lost_time_incident_count)
    display_name: "Lost Time Incident Count"
  - name: total_anomaly_count
    expr: SUM(source.total_anomaly_count)
    display_name: "Total Anomaly Count"
  - name: grid_instability_risk_score
    expr: |-
      100.0 * LEAST(1.0, (
        0.4 * SUM(source.total_forced_outage_count) / GREATEST(COUNT(*), 1) / 2.0 +
        0.3 * SUM(source.total_anomaly_count) / GREATEST(COUNT(*), 1) / 10.0 +
        0.3 * (100.0 - COALESCE(AVG(source.avg_efficiency_pct), 100.0)) / 30.0
      ))
    display_name: "Grid Instability Risk Score"
"""

spark.sql(f"""
CREATE OR REPLACE VIEW {CAT}.{SCH}.executive_summary_metrics
WITH METRICS LANGUAGE YAML AS $${EXEC_YAML}$$
""")
print("  executive_summary_metrics created")


print("\n=== All metric views created ===")
spark.stop()
