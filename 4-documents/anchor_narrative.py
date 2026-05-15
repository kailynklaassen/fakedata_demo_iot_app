"""
Pull concrete anchors from the workspace data to ground the synthetic documents
in real (synthetic) entity IDs, dates, and dollar values.
Writes a JSON 'narrative bible' to /tmp/narrative_bible.json.
"""
import os, json
from databricks.connect import DatabricksSession

CATALOG = globals().get("CATALOG", "serverless_stable_cgxfyd_catalog")
SCHEMA = globals().get("SCHEMA", "kailyn_klaassen")
PROFILE = globals().get("PROFILE", "fe-vm-serverless-stable-cgxfyd")
os.environ["DATABRICKS_CONFIG_PROFILE"] = PROFILE

spark = DatabricksSession.builder.profile(PROFILE).serverless().getOrCreate()
spark.sql(f"USE {CATALOG}.{SCHEMA}")

def to_rows(df):
    return [r.asDict() for r in df.collect()]

bible = {}

# 1. Worst problem assets across the year (outage volume + lost MWh + reactive WOs)
bible["problem_assets"] = to_rows(spark.sql("""
WITH wo_counts AS (
  SELECT asset_id, COUNT(*) AS reactive_emergency_wos
  FROM work_orders WHERE work_order_type IN ('emergency','reactive')
  GROUP BY asset_id
)
SELECT a.asset_id, a.asset_tag, a.asset_type, a.manufacturer,
       s.site_name, s.generation_type, r.region_name,
       COUNT(DISTINCT o.outage_id) AS forced_outages,
       ROUND(SUM(o.lost_generation_mwh), 0) AS total_lost_mwh,
       ROUND(SUM(o.lost_generation_mwh * 60), 0) AS est_revenue_loss_usd,
       COALESCE(MAX(wc.reactive_emergency_wos), 0) AS reactive_emergency_wos
FROM outages o
JOIN assets a USING(asset_id)
JOIN sites s ON a.site_id = s.site_id
JOIN regions r ON s.region_id = r.region_id
LEFT JOIN wo_counts wc ON a.asset_id = wc.asset_id
WHERE o.forced_outage_flag = true
GROUP BY a.asset_id, a.asset_tag, a.asset_type, a.manufacturer,
         s.site_name, s.generation_type, r.region_name
ORDER BY total_lost_mwh DESC LIMIT 25
"""))

# 2. NW-PowerPool specific
bible["nw_powerpool_outages"] = to_rows(spark.sql("""
SELECT DATE(o.outage_start_ts) AS outage_date,
       a.asset_tag, a.asset_type, a.manufacturer, s.site_name,
       o.outage_reason,
       CAST((UNIX_TIMESTAMP(o.outage_end_ts) - UNIX_TIMESTAMP(o.outage_start_ts))/3600.0 AS INT) AS duration_h,
       ROUND(o.lost_generation_mwh, 1) AS lost_mwh,
       o.outage_id
FROM outages o
JOIN assets a USING(asset_id)
JOIN sites s ON a.site_id = s.site_id
JOIN regions r ON s.region_id = r.region_id
WHERE r.region_name = 'NW-PowerPool' AND o.forced_outage_flag = true
ORDER BY o.lost_generation_mwh DESC LIMIT 20
"""))

# 3. Outage clustering by month — identify "major outage periods"
bible["monthly_outage_summary"] = to_rows(spark.sql("""
SELECT DATE_TRUNC('MONTH', o.outage_start_ts) AS month,
       r.region_name,
       COUNT(DISTINCT o.outage_id) AS forced_outages,
       ROUND(SUM(o.lost_generation_mwh), 0) AS total_lost_mwh
FROM outages o
JOIN assets a USING(asset_id)
JOIN sites s ON a.site_id = s.site_id
JOIN regions r ON s.region_id = r.region_id
WHERE o.forced_outage_flag = true
GROUP BY DATE_TRUNC('MONTH', o.outage_start_ts), r.region_name
ORDER BY month, total_lost_mwh DESC
"""))

# 4. Vendor (manufacturer) breakdown by reliability
bible["vendor_reliability"] = to_rows(spark.sql("""
WITH wo_by_mfr AS (
  SELECT a.manufacturer,
         COUNT(*) AS emergency_reactive_wo,
         ROUND(SUM(wo.parts_cost_usd), 0) AS emergency_parts_cost_usd
  FROM work_orders wo
  JOIN assets a ON wo.asset_id = a.asset_id
  WHERE wo.work_order_type IN ('emergency','reactive')
  GROUP BY a.manufacturer
)
SELECT a.manufacturer,
       a.asset_type,
       COUNT(DISTINCT a.asset_id) AS asset_count,
       COUNT(DISTINCT o.outage_id) AS forced_outages,
       ROUND(SUM(o.lost_generation_mwh), 0) AS total_lost_mwh,
       ROUND(AVG(o.lost_generation_mwh), 1) AS avg_lost_per_outage,
       MAX(w.emergency_reactive_wo) AS emergency_reactive_wo,
       MAX(w.emergency_parts_cost_usd) AS emergency_parts_cost_usd
FROM assets a
LEFT JOIN outages o ON a.asset_id = o.asset_id AND o.forced_outage_flag = true
LEFT JOIN wo_by_mfr w ON a.manufacturer = w.manufacturer
GROUP BY a.manufacturer, a.asset_type
ORDER BY total_lost_mwh DESC NULLS LAST
"""))

# 5. Worst outages overall — for doc anchoring
bible["worst_outages"] = to_rows(spark.sql("""
SELECT o.outage_id, DATE(o.outage_start_ts) AS outage_date,
       o.outage_start_ts, o.outage_end_ts,
       a.asset_id, a.asset_tag, a.asset_type, a.manufacturer,
       s.site_name, r.region_name, o.outage_reason,
       CAST((UNIX_TIMESTAMP(o.outage_end_ts) - UNIX_TIMESTAMP(o.outage_start_ts))/3600.0 AS INT) AS duration_h,
       ROUND(o.lost_generation_mwh, 1) AS lost_mwh
FROM outages o
JOIN assets a USING(asset_id)
JOIN sites s ON a.site_id = s.site_id
JOIN regions r ON s.region_id = r.region_id
WHERE o.forced_outage_flag = true
ORDER BY o.lost_generation_mwh DESC LIMIT 30
"""))

# 6. NW-PowerPool sites
bible["nw_sites"] = to_rows(spark.sql("""
SELECT s.site_id, s.site_name, s.generation_type, s.capacity_mw, s.commission_date
FROM sites s
JOIN regions r USING(region_id)
WHERE r.region_name = 'NW-PowerPool'
ORDER BY s.commission_date
"""))

# 7. NW-PowerPool financial perf
bible["regional_financials"] = to_rows(spark.sql("""
SELECT r.region_name,
       ROUND(SUM(af.revenue_usd), 0) AS revenue,
       ROUND(SUM(af.opex_usd), 0) AS opex,
       ROUND(SUM(af.maintenance_cost_usd), 0) AS maint_cost,
       ROUND(SUM(af.revenue_usd - af.opex_usd - af.maintenance_cost_usd), 0) AS net_profit,
       ROUND(100.0 * SUM(af.revenue_usd - af.opex_usd - af.maintenance_cost_usd) / NULLIF(SUM(af.revenue_usd),0), 1) AS margin_pct
FROM asset_financials af
JOIN assets a USING(asset_id)
JOIN sites s ON a.site_id = s.site_id
JOIN regions r ON s.region_id = r.region_id
GROUP BY r.region_name
ORDER BY net_profit
"""))

# 8. Find recurring offenders — assets with 3+ outages
bible["repeat_offenders"] = to_rows(spark.sql("""
SELECT a.asset_id, a.asset_tag, a.asset_type, a.manufacturer,
       s.site_name, r.region_name,
       COUNT(DISTINCT o.outage_id) AS forced_outages,
       MIN(DATE(o.outage_start_ts)) AS first_outage,
       MAX(DATE(o.outage_start_ts)) AS last_outage,
       ROUND(SUM(o.lost_generation_mwh), 0) AS total_lost_mwh
FROM outages o
JOIN assets a USING(asset_id)
JOIN sites s ON a.site_id = s.site_id
JOIN regions r ON s.region_id = r.region_id
WHERE o.forced_outage_flag = true
GROUP BY a.asset_id, a.asset_tag, a.asset_type, a.manufacturer, s.site_name, r.region_name
HAVING COUNT(DISTINCT o.outage_id) >= 3
ORDER BY forced_outages DESC, total_lost_mwh DESC LIMIT 20
"""))

# Serialize - convert dates to strings
def stringify(v):
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return v

def clean(rows):
    return [{k: stringify(v) for k, v in r.items()} for r in rows]

for k in bible:
    bible[k] = clean(bible[k])

with open("/tmp/narrative_bible.json", "w") as f:
    json.dump(bible, f, indent=2, default=str)

print("Wrote /tmp/narrative_bible.json")
for k, v in bible.items():
    print(f"  {k}: {len(v)} rows")
spark.stop()
