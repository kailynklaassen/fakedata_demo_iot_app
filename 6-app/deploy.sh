#!/bin/bash
# Deploy the Utility Operations Intelligence Assistant Databricks App.
# Idempotent — creates the app if missing, then syncs + deploys.
set -e

PROFILE="${PROFILE:-fe-vm-serverless-stable-cgxfyd}"
APP_NAME="${APP_NAME:-utility-ops-supervisor}"

# Auto-discover the user email from the CLI profile
EMAIL=$(databricks current-user me --profile="$PROFILE" --output=json | python3 -c "import json,sys;print(json.load(sys.stdin)['userName'])")
WORKSPACE_PATH="/Workspace/Users/$EMAIL/$APP_NAME"

echo "== Deploy config =="
echo "  Profile:        $PROFILE"
echo "  App name:       $APP_NAME"
echo "  Workspace path: $WORKSPACE_PATH"
echo

# 1. Create the app (skip if it already exists)
if databricks apps get "$APP_NAME" --profile="$PROFILE" --output=json >/dev/null 2>&1; then
  echo "✓ App '$APP_NAME' already exists"
else
  echo "Creating app '$APP_NAME'..."
  databricks apps create "$APP_NAME" \
    --description "Multi-source supervisor agent for utility operations (Genie + RAG)" \
    --profile="$PROFILE"
fi

# 2. Sync source
echo
echo "Syncing source -> $WORKSPACE_PATH ..."
databricks sync . "$WORKSPACE_PATH" --profile="$PROFILE"

# 3. Deploy
echo
echo "Deploying..."
databricks apps deploy "$APP_NAME" \
  --source-code-path "$WORKSPACE_PATH" \
  --profile="$PROFILE" | python3 -c "
import json, sys
d = json.load(sys.stdin)
status = d.get('status') or {}
print(f\"  deployment_id: {d.get('deployment_id')}\")
print(f\"  state:         {status.get('state')}\")
print(f\"  message:       {status.get('message')}\")
"

# 4. Print the URL
APP_URL=$(databricks apps get "$APP_NAME" --profile="$PROFILE" --output=json | python3 -c "import json,sys;print(json.load(sys.stdin).get('url',''))")
echo
echo "✓ App URL: $APP_URL"
