#!/usr/bin/env bash
# Creates GitHub issues for all findings from the code audit (issue #71).
# Requires: gh CLI authenticated against this repo.
# Usage: ./create-audit-issues.sh

set -euo pipefail

REPO="selmer/litterbox"
AUDIT_REF="Closes #71 (code audit)"

create() {
  local title="$1"
  local label="$2"
  local body="$3"
  echo "Creating: $title"
  gh issue create \
    --repo "$REPO" \
    --title "$title" \
    --label "$label" \
    --body "$body"
}

# ---------------------------------------------------------------------------
# CRITICAL SECURITY
# ---------------------------------------------------------------------------

create \
  "[security] Purge sensitive device credentials from git history" \
  "security" \
"## Problem
\`devices.json\`, \`snapshot.json\`, and \`tuya-raw.json\` were committed and are tracked in git even though they are in \`.gitignore\`. They expose:
- Device local encryption key (\`Wqgd^&nPvM:8Bjl|\`) — allows LAN device control
- Device ID, MAC address, UUID, serial number
- Home public IP address and Tuya account ID

## Action required
1. Purge these files from git history with BFG or \`git filter-repo\`.
2. Rotate the device local key in the Tuya app.
3. Verify \`.gitignore\` patterns cover all three filenames.

$AUDIT_REF"

create \
  "[security] Add authentication to all API endpoints" \
  "security" \
"## Problem
No authentication layer exists. Anyone who can reach port 8001 can read all data, create/delete visits, modify cats, and trigger manual operations.

## Suggested fix
Add HTTP Basic Auth, an API key header check, or a proper session mechanism via FastAPI middleware.

$AUDIT_REF"

create \
  "[security] Restrict CORS from wildcard to specific origins" \
  "security" \
"## Problem
\`app/main.py:59-64\` uses \`allow_origins=[\"*\"]\`. If Basic Auth or cookies are added later, this enables CSRF attacks from any origin.

## Suggested fix
Restrict to the actual frontend origin, e.g. \`[\"http://localhost:5173\"]\` for dev, and the production URL for prod.

$AUDIT_REF"

create \
  "[security] Remove default weak database password from docker-compose" \
  "security" \
"## Problem
\`docker-compose.yml:7\` defaults \`POSTGRES_PASSWORD\` to \`changeme\` and \`.env.example\` uses the same value. Many deployers will never change it.

## Suggested fix
Remove the default entirely so Docker Compose fails loudly when \`POSTGRES_PASSWORD\` is unset, and update \`.env.example\` with a clearly non-usable placeholder like \`POSTGRES_PASSWORD=CHANGE_ME_BEFORE_RUNNING\`.

$AUDIT_REF"

create \
  "[security] Move hardcoded NAS credentials out of deploy.sh" \
  "security" \
"## Problem
\`deploy.sh:4-6\` hardcodes NAS username, host IP, and path in a public repo.

## Suggested fix
Read these from environment variables or a local config file that is \`.gitignore\`d.

$AUDIT_REF"

create \
  "[security] deploy.sh blindly stages all files with git add -A" \
  "security" \
"## Problem
\`deploy.sh:33\` runs \`git add -A\`, which could accidentally commit \`.env\` files, secrets, or large binaries.

## Suggested fix
Stage only known-safe files explicitly (e.g. \`git add app/ frontend/ docker-compose.yml\`).

$AUDIT_REF"

# ---------------------------------------------------------------------------
# MEDIUM SECURITY
# ---------------------------------------------------------------------------

create \
  "[security] Add upper bound to limit query parameters" \
  "security" \
"## Problem
\`app/routers/visits.py:32\` and \`app/routers/cleaning_cycles.py:12\` accept \`limit\` with no maximum. A client can request \`limit=1000000\`, causing a large DB scan and memory spike.

## Suggested fix
\`\`\`python
limit: int = Query(default=100, ge=1, le=500)
\`\`\`

$AUDIT_REF"

create \
  "[security] Validate identified_by as an enum instead of a free-form string" \
  "security" \
"## Problem
\`app/models.py:45\` and \`app/schemas.py:55\` accept any string for \`identified_by\`. Business logic relies on the values \`\"auto\"\` and \`\"manual\"\`, so typos cause silent data corruption.

## Suggested fix
Use a Pydantic \`Literal[\"auto\", \"manual\"]\` in the schema and a PostgreSQL enum in the model.

$AUDIT_REF"

create \
  "[security] Serve the app over HTTPS" \
  "security" \
"## Problem
The app is served on plain HTTP on port 8001. Any future auth tokens or session cookies would be transmitted in cleartext.

## Suggested fix
Terminate TLS at the NAS reverse proxy (nginx/Caddy on Synology DSM) and redirect HTTP to HTTPS.

$AUDIT_REF"

# ---------------------------------------------------------------------------
# ARCHITECTURE
# ---------------------------------------------------------------------------

create \
  "[bug] Thread-unsafe shared mutable state for poller health timestamp" \
  "bug" \
"## Problem
\`app/routers/dashboard.py:16\` declares \`last_successful_poll_at\` as a module-level variable. It is written by the poller thread and read by HTTP handler threads without any lock — a data race.

## Suggested fix
Use \`threading.Lock\`, store the value in the database, or use an \`asyncio\`-safe primitive.

$AUDIT_REF"

create \
  "[architecture] Use a short-lived DB session per poll cycle in the poller" \
  "architecture" \
"## Problem
\`app/main.py:34\` creates a single \`SessionLocal()\` and keeps it alive across all polls. Stale SQLAlchemy identity-map data and dropped connections can cause inconsistent state.

## Suggested fix
Create a new short-lived session inside \`LitterboxPoller.poll()\` using a context manager, and close it after each cycle.

$AUDIT_REF"

create \
  "[performance] Fix N+1 query problem on the dashboard endpoint" \
  "performance" \
"## Problem
\`app/routers/dashboard.py:29-61\` executes 2N+3 queries per request (two per active cat). This degrades as the number of cats grows.

## Suggested fix
Replace per-cat queries with a single \`JOIN\` using \`func.count\`, \`func.sum\`, and a subquery/lateral for the last visit timestamp.

$AUDIT_REF"

create \
  "[bug] Remove __import__('datetime') hack in poller.py" \
  "bug" \
"## Problem
\`app/poller.py:143\` uses \`__import__('datetime').timedelta(...)\` because \`timedelta\` was not imported.

## Suggested fix
\`\`\`python
from datetime import datetime, timezone, timedelta
\`\`\`
Then use \`timedelta\` directly.

$AUDIT_REF"

create \
  "[architecture] Add retention/cleanup policy for DeviceSnapshot and SettingsHistory tables" \
  "architecture" \
"## Problem
\`DeviceSnapshot\` accumulates ~288 rows/day and \`SettingsHistory\` rows are never deleted. After months of operation these become large, never-queried tables.

## Suggested fix
Add a scheduled cleanup job (e.g. APScheduler or a cron in Docker) to delete rows older than 30 days.

$AUDIT_REF"

create \
  "[architecture] Expose SettingsHistory via an API or remove the table" \
  "architecture" \
"## Problem
\`app/models.py:76\` has a comment \"store as string, parse on read\" but there is no read endpoint for \`SettingsHistory\` anywhere. Data is written but never surfaced.

## Suggested fix
Either add a \`GET /settings-history\` endpoint or remove the table and \`_record_setting_change\` calls to reduce confusion.

$AUDIT_REF"

create \
  "[architecture] Implement cat photo backend storage or remove the upload UI" \
  "architecture" \
"## Problem
\`frontend/src/components/CatPhotoUpload.jsx\` implements crop/compress UI and calls \`onSave(preview)\` with a base64 data URL, but there is no API endpoint, no model field, and no storage backend. The \`.gitignore\` mentions \`uploads/cat_photos/\` as if this was planned.

## Suggested fix
Either implement a \`POST /cats/{id}/photo\` endpoint with file storage, or remove \`CatPhotoUpload\` until the feature is ready.

$AUDIT_REF"

create \
  "[bug] Dashboard 'today' uses UTC instead of local time" \
  "bug" \
"## Problem
\`app/routers/dashboard.py:24\` computes midnight in UTC. Users outside UTC see a mismatched \"today\".

## Suggested fix
Accept a \`timezone\` query parameter (e.g. \`+01:00\`) and compute local midnight accordingly. The device timezone is already available in \`tuya-raw.json\`.

$AUDIT_REF"

create \
  "[architecture] Consolidate alembic engine to reuse app/database.py settings" \
  "architecture" \
"## Problem
\`alembic/env.py:61\` instantiates a raw \`create_engine(DATABASE_URL)\` instead of importing from \`app/database\`. Pool settings like \`pool_pre_ping=True\` are not applied during migrations.

## Suggested fix
Import and reuse the engine from \`app/database\` in \`alembic/env.py\`.

$AUDIT_REF"

create \
  "[architecture] Add offset or cursor pagination to the visits endpoint" \
  "architecture" \
"## Problem
\`app/routers/visits.py:31\` supports \`limit\` but no \`offset\` or cursor. The frontend hardcodes \`limit=100\`. Users with many visits are silently capped.

## Suggested fix
Add an \`offset: int = Query(default=0, ge=0)\` parameter and return the total count in the response so the frontend can paginate.

$AUDIT_REF"

create \
  "[cleanup] Consolidate duplicate env example files" \
  "cleanup" \
"## Problem
Both \`env-example\` and \`.env.example\` exist at the repo root with the same content, and a third copy is in \`tools/\`.

## Suggested fix
Keep only \`.env.example\` at the root, remove the others, and update any README references.

$AUDIT_REF"

create \
  "[architecture] Derive poller health threshold from POLL_INTERVAL_SECONDS" \
  "architecture" \
"## Problem
\`app/routers/dashboard.py:13\` hardcodes \`POLLER_HEALTHY_THRESHOLD_SECONDS = 30\` while \`docker-compose.yml\` sets \`POLL_INTERVAL_SECONDS=5\`. If the interval is changed, health detection breaks silently.

## Suggested fix
\`\`\`python
POLLER_HEALTHY_THRESHOLD_SECONDS = int(os.getenv(\"POLL_INTERVAL_SECONDS\", 5)) * 3
\`\`\`

$AUDIT_REF"

create \
  "[bug] TypeError when identified_by receives None weight in _identify_visit_cat" \
  "bug" \
"## Problem
\`app/poller.py:189\` calls \`identify_cat(weight_kg, ...)\` where \`weight_kg\` can be \`None\`. \`identify_cat\` checks \`if weight_kg <= 0\` which raises \`TypeError: '<=' not supported between instances of 'NoneType' and 'int'\` in Python 3.

## Suggested fix
Add a \`None\` guard at the top of \`_identify_visit_cat\` or inside \`identify_cat\`:
\`\`\`python
if weight_kg is None or weight_kg <= 0:
    ...
\`\`\`

$AUDIT_REF"

create \
  "[cleanup] Remove committed bfg-1.14.0.jar binary from the repo" \
  "cleanup" \
"## Problem
\`bfg-1.14.0.jar\` (~14 MB Java binary) is committed to the repo. Binaries should not live in version control.

## Suggested fix
Remove it with \`git rm bfg-1.14.0.jar\`, add \`*.jar\` to \`.gitignore\`, and document the intended BFG usage in the README.

$AUDIT_REF"

# ---------------------------------------------------------------------------
# MINOR / CODE QUALITY
# ---------------------------------------------------------------------------

create \
  "[cleanup] Move HTTPException import to top-level in visits.py" \
  "cleanup" \
"## Problem
\`app/routers/visits.py\` imports \`HTTPException\` inside individual function bodies multiple times instead of at the module level.

## Suggested fix
Add \`from fastapi import HTTPException\` at the top of the file and remove the inline imports.

$AUDIT_REF"

create \
  "[ux] Surface API errors to the user in the frontend" \
  "ux" \
"## Problem
- \`frontend/src/pages/Visits.jsx:27\`: \`handleDelete\` catches errors and only logs to console.
- \`frontend/src/pages/Cats.jsx:84-99\`: \`handleCreate\`/\`handleUpdate\`/\`handleToggleActive\` have no error handling at all.

Failed API calls silently leave the UI in a stale state.

## Suggested fix
Show a toast or inline error message when API calls fail.

$AUDIT_REF"

create \
  "[bug] Startup cleanup for visits with ended_at IS NULL" \
  "bug" \
"## Problem
If the app crashes between a weight event and the completion event, the DB will have a perpetually-open visit with \`ended_at = NULL\`.

## Suggested fix
Add a startup query that closes any visits where \`ended_at IS NULL\` and \`started_at < NOW() - INTERVAL 'VISIT_TIMEOUT_SECONDS seconds'\`.

$AUDIT_REF"

create \
  "[performance] Add DB indexes on Visit.started_at and Visit.cat_id" \
  "performance" \
"## Problem
\`app/models.py:46-47\` — \`started_at\` and \`cat_id\` are heavily filtered in dashboard and visit queries but have no index defined.

## Suggested fix
\`\`\`python
cat_id = Column(Integer, ForeignKey(\"cats.id\"), index=True)
started_at = Column(DateTime(timezone=True), index=True)
\`\`\`
And generate a corresponding Alembic migration.

$AUDIT_REF"

echo ""
echo "Done! All audit issues have been created."
