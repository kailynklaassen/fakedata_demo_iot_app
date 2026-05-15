"""
Sanity SQL — validates causal chains and signal patterns in the generated dataset.
"""
import os
from databricks.connect import DatabricksSession

PROFILE = globals().get("PROFILE", "fe-vm-serverless-stable-cgxfyd")
CATALOG = globals().get("CATALOG", "serverless_stable_cgxfyd_catalog")
SCHEMA = globals().get("SCHEMA", "kailyn_klaassen")
os.environ["DATABRICKS_CONFIG_PROFILE"] = PROFILE

spark = DatabricksSession.builder.profile(PROFILE).serverless().getOrCreate()
spark.sql(f"USE {CATALOG}.{SCHEMA}")


def run(title, sql):
    print(f"\n--- {title} ---")
    rows = spark.sql(sql).collect()
    if not rows:
        print("  (no rows)")
        return
    cols = rows[0].asDict().keys()
    print("  " + " | ".join(f"{c:>22}" for c in cols))
    for r in rows[:40]:
        print("  " + " | ".join(f"{str(r[c]):>22}" for c in cols))


# 1. Asset type counts
run("Asset mix", """
SELECT asset_type, COUNT(*) AS n, ROUND(AVG(criticality_score), 2) AS avg_crit
FROM assets GROUP BY asset_type ORDER BY n DESC
""")

# 2. Site mix by region & generation_type
run("Sites by region × type", """
SELECT r.region_name, s.generation_type, COUNT(*) AS n_sites, ROUND(SUM(s.capacity_mw), 0) AS total_mw
FROM sites s JOIN regions r USING(region_id)
GROUP BY r.region_name, s.generation_type ORDER BY r.region_name, s.generation_type
""")

# 3. Market price seasonality: monthly avg per region (top 3 regions)
run("Market price by month (CAISO / ERCOT / NYISO)", """
SELECT r.region_name,
       MONTH(timestamp) AS month,
       ROUND(AVG(real_time_price_mwh), 2) AS avg_price
FROM market_prices mp JOIN regions r USING(region_id)
WHERE r.region_name IN ('CAISO','ERCOT','NYISO')
GROUP BY r.region_name, MONTH(timestamp)
ORDER BY r.region_name, month
""")

# 4. Market price evening-peak pattern (avg by hour-of-day for CAISO)
run("CAISO price by hour-of-day", """
SELECT HOUR(timestamp) AS hour, ROUND(AVG(real_time_price_mwh), 2) AS avg_price
FROM market_prices mp JOIN regions r USING(region_id)
WHERE r.region_name = 'CAISO'
GROUP BY HOUR(timestamp) ORDER BY hour
""")

# 5. Anomaly frequency vs outage rate (causal chain part 1)
run("Anomaly -> outage conversion rate", """
WITH per_asset AS (
  SELECT a.asset_id,
         COUNT(DISTINCT sa.anomaly_id) AS anomalies,
         COUNT(DISTINCT o.outage_id) AS outages
  FROM assets a
  LEFT JOIN sensor_anomalies sa ON a.asset_id = sa.asset_id
  LEFT JOIN outages o ON a.asset_id = o.asset_id AND o.forced_outage_flag = true
  GROUP BY a.asset_id
)
SELECT
  CASE WHEN anomalies = 0 THEN '0' WHEN anomalies <= 2 THEN '1-2'
       WHEN anomalies <= 5 THEN '3-5' WHEN anomalies <= 15 THEN '6-15'
       ELSE '16+' END AS anomaly_bucket,
  COUNT(*) AS n_assets,
  ROUND(AVG(outages), 2) AS avg_forced_outages
FROM per_asset
GROUP BY anomaly_bucket
ORDER BY anomaly_bucket
""")

# 6. Outage outcomes: lost generation by outage reason (causal chain part 2)
run("Lost generation by outage reason", """
SELECT outage_reason,
       COUNT(*) AS n_outages,
       ROUND(AVG(lost_generation_mwh), 1) AS avg_lost_mwh,
       ROUND(SUM(lost_generation_mwh), 0) AS total_lost_mwh
FROM outages
GROUP BY outage_reason
ORDER BY total_lost_mwh DESC
""")

# 7. Emergency work_orders link back to outages (causal chain part 3)
run("Work order types — outage linkage", """
SELECT work_order_type,
       COUNT(*) AS n,
       ROUND(AVG(labor_hours), 1) AS avg_labor,
       ROUND(AVG(parts_cost_usd), 0) AS avg_parts_cost,
       ROUND(100.0 * SUM(CASE WHEN outage_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_with_outage_link
FROM work_orders
GROUP BY work_order_type
ORDER BY n DESC
""")

# 8. Revenue impact: outage during high-price hour (causal chain part 4)
run("Revenue impact of high-price-hour outages", """
WITH outage_hours AS (
  SELECT o.outage_id, o.asset_id, a.site_id, s.region_id,
         o.outage_start_ts, o.outage_end_ts, o.lost_generation_mwh
  FROM outages o
  JOIN assets a USING(asset_id)
  JOIN sites s ON a.site_id = s.site_id
), price_at_outage AS (
  SELECT oh.outage_id,
         oh.lost_generation_mwh,
         AVG(mp.real_time_price_mwh) AS avg_price_during
  FROM outage_hours oh
  JOIN market_prices mp
    ON mp.region_id = oh.region_id
   AND mp.timestamp >= date_trunc('HOUR', oh.outage_start_ts)
   AND mp.timestamp <  oh.outage_end_ts
  GROUP BY oh.outage_id, oh.lost_generation_mwh
)
SELECT
  CASE WHEN avg_price_during < 35 THEN 'low (<$35)'
       WHEN avg_price_during < 50 THEN 'mid ($35-50)'
       WHEN avg_price_during < 65 THEN 'high ($50-65)'
       ELSE 'peak ($65+)' END AS price_bucket,
  COUNT(*) AS n_outages,
  ROUND(AVG(lost_generation_mwh), 1) AS avg_lost_mwh,
  ROUND(AVG(lost_generation_mwh * avg_price_during), 0) AS avg_revenue_loss_usd,
  ROUND(SUM(lost_generation_mwh * avg_price_during), 0) AS total_revenue_loss_usd
FROM price_at_outage
GROUP BY price_bucket
ORDER BY total_revenue_loss_usd DESC
""")

# 9. Asset age correlates with operational degradation
run("Asset age vs financials", """
SELECT
  CASE WHEN DATEDIFF(CURRENT_DATE(), a.install_date) / 365 < 5 THEN '<5y'
       WHEN DATEDIFF(CURRENT_DATE(), a.install_date) / 365 < 10 THEN '5-10y'
       WHEN DATEDIFF(CURRENT_DATE(), a.install_date) / 365 < 15 THEN '10-15y'
       ELSE '15y+' END AS age_bucket,
  COUNT(DISTINCT a.asset_id) AS n_assets,
  ROUND(AVG(f.profit_margin_pct), 1) AS avg_margin,
  ROUND(AVG(f.revenue_usd), 0) AS avg_daily_rev,
  ROUND(AVG(f.maintenance_cost_usd), 0) AS avg_daily_maint
FROM assets a JOIN asset_financials f USING(asset_id)
GROUP BY age_bucket
ORDER BY age_bucket
""")

# 10. Time alignment check: anomaly -> outage -> work order
run("Causal chain time alignment (samples)", """
WITH anom_to_outage AS (
  SELECT sa.anomaly_id, sa.asset_id, sa.timestamp AS anom_ts, sa.severity_score,
         o.outage_id, o.outage_start_ts,
         CAST((UNIX_TIMESTAMP(o.outage_start_ts) - UNIX_TIMESTAMP(sa.timestamp))/3600 AS INT) AS lag_hours
  FROM sensor_anomalies sa
  JOIN outages o ON sa.asset_id = o.asset_id
  WHERE o.outage_start_ts BETWEEN sa.timestamp AND sa.timestamp + INTERVAL 48 HOURS
    AND o.forced_outage_flag = true
), with_wo AS (
  SELECT ato.*, wo.work_order_id, wo.work_order_type, wo.created_ts,
         CAST((UNIX_TIMESTAMP(wo.created_ts) - UNIX_TIMESTAMP(ato.outage_start_ts))/3600 AS INT) AS wo_lag_hours
  FROM anom_to_outage ato
  LEFT JOIN work_orders wo ON ato.outage_id = wo.outage_id
)
SELECT severity_score, lag_hours, work_order_type, wo_lag_hours
FROM with_wo WHERE work_order_type IS NOT NULL
ORDER BY severity_score DESC LIMIT 15
""")

# 11. Maintenance affects reliability (overdue/uncompleted -> more outages?)
run("Overdue maintenance correlates with outages", """
WITH ms_status AS (
  SELECT asset_id,
         SUM(CASE WHEN overdue_flag THEN 1 ELSE 0 END) AS overdue_n,
         SUM(CASE WHEN completed_flag THEN 1 ELSE 0 END) AS completed_n,
         COUNT(*) AS total_n
  FROM maintenance_schedule GROUP BY asset_id
), out_count AS (
  SELECT asset_id, COUNT(*) AS forced_outages
  FROM outages WHERE forced_outage_flag = true GROUP BY asset_id
)
SELECT
  CASE WHEN ms.overdue_n = 0 THEN 'none overdue'
       WHEN ms.overdue_n <= 1 THEN '1 overdue'
       WHEN ms.overdue_n <= 3 THEN '2-3 overdue'
       ELSE '4+ overdue' END AS overdue_bucket,
  COUNT(*) AS n_assets,
  ROUND(AVG(COALESCE(oc.forced_outages, 0)), 2) AS avg_forced_outages
FROM ms_status ms LEFT JOIN out_count oc USING(asset_id)
GROUP BY overdue_bucket
ORDER BY overdue_bucket
""")

# 12. Sample joined view (Genie-friendly)
run("Genie-friendly sample: outage with surroundings", """
SELECT o.outage_id, a.asset_type, s.site_name, r.region_name,
       o.outage_start_ts, o.outage_reason,
       ROUND(o.lost_generation_mwh, 1) AS lost_mwh,
       wo.work_order_type, wo.priority
FROM outages o
JOIN assets a USING(asset_id)
JOIN sites s ON a.site_id = s.site_id
JOIN regions r ON s.region_id = r.region_id
LEFT JOIN work_orders wo ON o.outage_id = wo.outage_id
WHERE o.lost_generation_mwh > 200
ORDER BY o.lost_generation_mwh DESC LIMIT 10
""")

spark.stop()
