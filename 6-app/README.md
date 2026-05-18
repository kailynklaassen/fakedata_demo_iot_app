# 6 — Databricks App (branded UI)

A FastAPI + static-HTML Databricks App that talks to the supervisor multi-agent system from step 5. Includes a neutral blue/green color palette, a placeholder logo, live response streaming, in-app Q&A cache, and a live "Routing & Sources" inspector panel showing exactly which tools the supervisor called. Swap the logo and CSS variables to brand it for any customer.

## Files

```
6-app/
├── README.md
├── app.py             FastAPI backend — proxies to supervisor, streams SSE, caches Q&A
├── app.yaml           Databricks Apps run config (command + env vars)
├── requirements.txt   Python deps
├── deploy.sh          One-command sync + deploy
├── .gitignore         excludes wireframe artifacts and pycache
└── static/
    ├── index.html     UI layout
    ├── style.css      themable styles (blue/green palette via CSS variables)
    ├── app.js         Frontend — live streaming render, polling, cache rendering
    └── logo.png       placeholder logo — replace with your branding
```

## What the app does

| Feature | Implementation |
| --- | --- |
| **Question routing** | `POST /api/chat` kicks off a background thread, returns a `job_id` immediately |
| **Live streaming** | Background thread consumes Server-Sent Events from the supervisor endpoint and updates `partial_answer` + `partial_trace` in-place; frontend polls `GET /api/chat/{job_id}` every 1.2s |
| **Cache** | In-memory LRU keyed by hash of `(history + question)`, 1 hour TTL, 100 entries. Cache hits respond in <1s with a `⚡ Cached` badge |
| **Trace panel** | Real-time render of supervisor steps: intent classify → tool calls → tool results → synthesis. Each tool call is color-coded (blue for Genie spaces, green for the Knowledge Assistant) |
| **Health** | `GET /healthz` returns `{ok, endpoint}` |
| **Cache reset** | `POST /api/cache/clear` evicts all cached entries |

## Prerequisites

1. Steps 1-5 complete (data, metric views, Genie spaces, PDFs, supervisor endpoint).
2. Databricks CLI v0.296+ authenticated to your workspace.
3. A user account or PAT that can create Databricks Apps.

## Configure

Edit `app.yaml` if your supervisor endpoint has a different name:

```yaml
env:
  - name: "SUPERVISOR_ENDPOINT"
    value: "mas-cf2369f5-endpoint"   # ← change to your endpoint
```

## Deploy

### One-liner

```bash
bash deploy.sh
```

This script:
1. Creates the app (idempotent — skips if already exists)
2. Syncs the source to a workspace path
3. Deploys the source
4. Prints the URL

### Manual steps

```bash
PROFILE=<your-profile>
APP_NAME=utility-ops-supervisor
EMAIL=<your-databricks-email>

# 1. Create the app (one-time)
databricks apps create $APP_NAME \
  --description "Multi-source supervisor agent for utility operations" \
  --profile=$PROFILE

# 2. Sync source code to workspace
databricks sync . /Workspace/Users/$EMAIL/$APP_NAME --profile=$PROFILE

# 3. Deploy
databricks apps deploy $APP_NAME \
  --source-code-path /Workspace/Users/$EMAIL/$APP_NAME \
  --profile=$PROFILE
```

## Grant the app's service principal access to downstream resources

The app runs as its own service principal. Grant it permissions on everything it needs to reach:

```bash
PROFILE=<your-profile>
SP=$(databricks apps get $APP_NAME --profile=$PROFILE --output=json | \
     python3 -c "import json,sys;print(json.load(sys.stdin)['service_principal_client_id'])")

# 1. CAN_QUERY on the supervisor + knowledge assistant endpoints
for ENDPOINT in mas-cf2369f5-endpoint ka-d6dd1932-endpoint; do
  EID=$(databricks serving-endpoints get $ENDPOINT --profile=$PROFILE --output=json | python3 -c "import json,sys;print(json.load(sys.stdin)['id'])")
  cat > /tmp/p.json << EOF
{"access_control_list":[{"service_principal_name":"$SP","permission_level":"CAN_QUERY"}]}
EOF
  databricks api patch "/api/2.0/permissions/serving-endpoints/$EID" --profile=$PROFILE --json @/tmp/p.json
done

# 2. CAN_RUN on each Genie space (replace with your space IDs)
for SID in <grid_space_id> <financial_space_id> <maintenance_space_id>; do
  cat > /tmp/p.json << EOF
{"access_control_list":[{"service_principal_name":"$SP","permission_level":"CAN_RUN"}]}
EOF
  databricks api patch "/api/2.0/permissions/genie/$SID" --profile=$PROFILE --json @/tmp/p.json
done

# 3. CAN_USE on the SQL warehouse (replace ID)
cat > /tmp/p.json << EOF
{"access_control_list":[{"service_principal_name":"$SP","permission_level":"CAN_USE"}]}
EOF
databricks api patch "/api/2.0/permissions/warehouses/<warehouse_id>" --profile=$PROFILE --json @/tmp/p.json

# 4. UC catalog + schema access
cat > /tmp/cat_grant.json << EOF
{"changes":[{"principal":"$SP","add":["USE_CATALOG","USE_SCHEMA","SELECT","READ_VOLUME","EXECUTE"]}]}
EOF
databricks api patch "/api/2.1/unity-catalog/permissions/catalog/<your_catalog>" --profile=$PROFILE --json @/tmp/cat_grant.json

cat > /tmp/sch_grant.json << EOF
{"changes":[{"principal":"$SP","add":["USE_SCHEMA","SELECT","READ_VOLUME","EXECUTE"]}]}
EOF
databricks api patch "/api/2.1/unity-catalog/permissions/schema/<your_catalog>.<your_schema>" --profile=$PROFILE --json @/tmp/sch_grant.json
```

## Verify

```bash
# Health
TOKEN=$(databricks auth token --profile=$PROFILE | jq -r .access_token)
APP_URL=$(databricks apps get $APP_NAME --profile=$PROFILE --output=json | jq -r .url)
curl -sk -H "Authorization: Bearer $TOKEN" "$APP_URL/healthz"

# Chat smoke test
curl -sk -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"message":"List the top 5 outages by lost MWh"}' \
  "$APP_URL/api/chat"
# returns {"job_id":"...","status":"running"}
```

Then open the app URL in a browser — auth uses your workspace SSO.

## Iterating on the UI

```bash
# Edit static/index.html, style.css, app.js (or backend app.py)
# Then:
bash deploy.sh
# OR
databricks sync . /Workspace/Users/$EMAIL/$APP_NAME --profile=$PROFILE
databricks apps deploy $APP_NAME --source-code-path /Workspace/Users/$EMAIL/$APP_NAME --profile=$PROFILE
```

Hard-refresh the browser (Cmd+Shift+R / Ctrl+Shift+R) after each deploy to bust the cached `app.js`.

## Local dev (optional)

You can run the app locally against your real supervisor endpoint:

```bash
export DATABRICKS_CONFIG_PROFILE=<your-profile>
export SUPERVISOR_ENDPOINT=mas-cf2369f5-endpoint
uv run --python 3.12 \
  --with fastapi --with 'uvicorn[standard]' \
  --with 'databricks-sdk>=0.30.0' --with requests --with pydantic \
  uvicorn app:app --reload --port 8000
```

Open http://localhost:8000. The Databricks SDK will pick up your local CLI auth.

## Rebranding for a different customer

1. Replace `static/logo.png` (the "Add Logo Here" placeholder) with the customer's logo. Recommended dimensions ~640 × 283 px with a transparent background; the header CSS auto-scales height to 44 px.
2. Edit the CSS variables at the top of `static/style.css`:

   ```css
   :root {
     --nx-blue: #2090D0;   /* primary action color */
     --nx-green: #60C020;  /* secondary / RAG accents */
     --nx-dark: #1A1A1A;   /* primary text */
     ...
   }
   ```

3. Edit the app title in `static/index.html` (`<title>` and `.app-title`).
4. Redeploy.

## Known constraints

- **Databricks Apps gateway timeout** (~60s) is bypassed by the async job + poll pattern. The frontend's hard ceiling is 10 minutes.
- **In-process cache** — restarts the app empties the cache. Acceptable for demos; for prod, swap in Redis.
- **Single replica** — the in-memory job store doesn't replicate. Fine for single-user demos; multi-replica would need shared state.
