# 3 — Create the 3 Genie Spaces

Authors 3 curated Genie Spaces — one per business domain — using the `GenieSpaceBuilder` helper from the `fe-internal-tools:genie-rooms` skill.

## What gets created

| Space | Primary Metric View | Sample tables also exposed |
| --- | --- | --- |
| **Grid Operations Intelligence** | `grid_operations_metrics` | `sensor_anomalies`, `outages`, `telemetry`, `assets`, `sites`, `regions` |
| **Energy Financial Performance Intelligence** | `financial_performance_metrics` | `asset_financials`, `power_sales`, `market_prices`, `outages` + dims |
| **Maintenance and Workforce Operations Intelligence** | `maintenance_workforce_metrics` | `work_orders`, `maintenance_schedule`, `safety_incidents`, `technicians` + dims |

Each space includes:
- A **system prompt** scoping the assistant's role + redirect rules to the other spaces
- 6 **certified example SQL questions** demonstrating the `MEASURE()` pattern
- The metric view + supporting raw tables as curated data sources

## Pre-requisites

- The Genie Space Builder helper from the vibe `fe-internal-tools` plugin. The script references it at:
  ```python
  sys.path.insert(0, "/Users/<you>/.vibe/marketplace/plugins/fe-internal-tools/skills/genie-rooms/resources")
  from genie_space_builder import GenieSpaceBuilder
  ```
  If you don't have vibe, copy `genie_space_builder.py` from that path into this folder and update the import.
- A SQL warehouse to attach. The script defaults to `7e4da1bdd34b875f` (Serverless Starter); change `WAREHOUSE_ID` if you use a different one.

## Configure

Edit `build_genie_spaces.py`:
```python
CAT = "serverless_stable_cgxfyd_catalog"
SCH = "kailyn_klaassen"
WAREHOUSE_ID = "7e4da1bdd34b875f"
USER_EMAIL = "you@databricks.com"
PARENT_PATH = f"/Workspace/Users/{USER_EMAIL}"
```

## Run

You can run either `build_genie_spaces.ipynb` as a Databricks notebook (Run All) or locally:

```bash
python3 build_genie_spaces.py
# → /tmp/grid_create.json, /tmp/fin_create.json, /tmp/maint_create.json
```

Either approach builds three `serialized_space` JSON files plus three "create-payload" JSON files in `/tmp/`.

Then POST each one to the Genie API:

```bash
PROFILE=fe-vm-serverless-stable-cgxfyd
databricks api post /api/2.0/genie/spaces --profile=$PROFILE --json @/tmp/grid_create.json
databricks api post /api/2.0/genie/spaces --profile=$PROFILE --json @/tmp/fin_create.json
databricks api post /api/2.0/genie/spaces --profile=$PROFILE --json @/tmp/maint_create.json
```

Each call returns a JSON with `space_id`. Save those — the supervisor model (step 5) will reference them by ID.

The Genie space URL pattern is:
```
https://<workspace-host>/genie/rooms/<space_id>
```

## Editing after creation

To edit an existing space, fetch it, modify, and PATCH back:

```bash
# Fetch
databricks api get "/api/2.0/genie/spaces/<space_id>?include_serialized_space=true" --profile=$PROFILE > /tmp/current.json
# (modify in your editor or with GenieSpaceBuilder.from_json)
# Patch
databricks api patch "/api/2.0/genie/spaces/<space_id>" --profile=$PROFILE --json @/tmp/updated.json
```

## Common adjustments

- Add a 4th space for `executive_summary_metrics` if you want a separate executive view. The script intentionally exposes the executive view *through* the supervisor model rather than as its own Genie space.
- Add more certified questions: copy any of the existing `add_example_sql(...)` blocks and customize.
- Change the system prompt: edit the `set_instructions("""...""")` argument for each builder.

## Validation rules the API enforces

- `data_sources.tables` must be sorted by `identifier` (the builder handles this)
- `example_question_sqls` must be sorted by `id` (the script's `sort_by_id_and_dump` handles this)
- Benchmark `format` enum is restricted (SQL is accepted; TEXT is not). The script does not emit benchmarks for this reason.
