#!/bin/bash
set -e
REPO="selmer/litterbox"

echo "Creating GitHub issues for code audit findings..."

# Issue 1 - Critical Security
gh issue create --repo "$REPO" \
  --title "[Security/Critical] Sensitive device credentials committed to git history" \
  --body "## Description

Files \`devices.json\`, \`snapshot.json\`, and \`tuya-raw.json\` are in \`.gitignore\` but were already committed and are tracked in git. They expose device local encryption keys, device IDs, MAC addresses, home public IP address, and Tuya account ID.

The presence of \`bfg-1.14.0.jar\` suggests an attempt to purge history was planned but not completed.

## Action Required

1. Purge these files from git history using BFG or \`git filter-repo\`
2. Rotate the device local key in the Tuya app
3. Verify \`.gitignore\` patterns cover these files

_From code audit in https://github.com/selmer/litterbox/issues/71_"

# Issue 2 - Critical Security
gh issue create --repo "$REPO" \
  --title "[Security/Critical] No authentication on any API endpoint" \
  --body "## Description

The API has no auth layer whatsoever. Anyone who can reach port 8001 can read all data, create/delete visits, modify cats, and trigger manual operations. If the NAS is ever port-forwarded or accessible via a VPN, this is fully open.

## Suggested Fix

Consider adding HTTP Basic Auth, an API key header check, or a proper session mechanism via FastAPI middleware.

_From code audit in https://github.com/selmer/litterbox/issues/71_"

# Issue 3 - Critical Security
gh issue create --repo "$REPO" \
  --title "[Security/Critical] Wildcard CORS allows any origin (app/main.py)" \
  --body "## Description

\`app/main.py:59-64\` uses \`allow_origins=[\"*\"]\`, which allows any website to make credentialed requests to the API. For a home application this is lower risk, but if Basic Auth or cookies are ever added, this becomes a serious vulnerability (CSRF).

## Suggested Fix

Restrict to the specific frontend origin or \`[\"http://localhost:5173\"]\` for dev.

_From code audit in https://github.com/selmer/litterbox/issues/71_"

# Issue 4 - Critical Security
gh issue create --repo "$REPO" \
  --title "[Security/Critical] Default weak database password in docker-compose.yml" \
  --body "## Description

\`docker-compose.yml:7\` uses \`\${POSTGRES_PASSWORD:-changeme}\`. Many users deploying this will never change the default. The \`.env.example\` also has \`POSTGRES_PASSWORD=changeme\`.

## Suggested Fix

Remove the default entirely (fail loudly if unset) or use a generated placeholder that clearly cannot be used as-is.

_From code audit in https://github.com/selmer/litterbox/issues/71_"

# Issue 5 - Critical Security
gh issue create --repo "$REPO" \
  --title "[Security/Critical] Hardcoded infrastructure details in deploy.sh" \
  --body "## Description

\`deploy.sh:4-6\` has NAS user, host IP, and path hardcoded:

\`\`\`bash
NAS_USER=\"selmer\"
NAS_HOST=\"192.168.68.115\"
NAS_PATH=\"/volume2/docker/litterbox\"
\`\`\`

Internal IPs and credentials-adjacent info should not be in a public repo.

## Suggested Fix

Move to environment variables or a local config file that is \`.gitignore\`d.

_From code audit in https://github.com/selmer/litterbox/issues/71_"

# Issue 6 - Critical Security
gh issue create --repo "$REPO" \
  --title "[Security/Critical] deploy.sh uses 'git add -A' blindly before committing" \
  --body "## Description

\`deploy.sh:33\` blindly stages all changes with \`git add -A\`. This could accidentally commit \`.env\` files, secrets, or large binaries if they somehow end up untracked.

## Suggested Fix

Stage only known safe files explicitly rather than using \`git add -A\`.

_From code audit in https://github.com/selmer/litterbox/issues/71_"

# Issue 7 - Medium Security
gh issue create --repo "$REPO" \
  --title "[Security/Medium] No input bounds on 'limit' query parameters" \
  --body "## Description

\`app/routers/visits.py:32\` and \`app/routers/cleaning_cycles.py:12\` accept \`limit\` with no maximum. A client can request \`limit=1000000\`, causing a large DB scan and potential memory spike.

## Suggested Fix

Add a \`Query(le=500)\` annotation to cap the maximum limit.

_From code audit in https://github.com/selmer/litterbox/issues/71_"

# Issue 8 - Medium Security
gh issue create --repo "$REPO" \
  --title "[Security/Medium] identified_by is a free-form string with no validation" \
  --body "## Description

\`app/models.py:45\` and \`app/schemas.py:55\` — \`identified_by\` accepts any string. If business logic relies on the values \`\"auto\"\` or \`\"manual\"\`, this should be a Pydantic \`Literal[\"auto\", \"manual\"]\` or a DB enum to prevent silent corruption from typos.

_From code audit in https://github.com/selmer/litterbox/issues/71_"

# Issue 9 - Medium Security
gh issue create --repo "$REPO" \
  --title "[Security/Medium] No HTTPS — traffic is unencrypted" \
  --body "## Description

The app is served on plain HTTP on port 8001. Even for home use, traffic (including any future auth tokens) is unencrypted.

## Suggested Fix

Consider terminating TLS at the NAS's reverse proxy (e.g., nginx/Caddy on Synology DSM).

_From code audit in https://github.com/selmer/litterbox/issues/71_"

# Issue 10 - Architecture
gh issue create --repo "$REPO" \
  --title "[Architecture] Thread-unsafe shared mutable state for poller health" \
  --body "## Description

\`app/routers/dashboard.py:16\` declares \`last_successful_poll_at: datetime = None\` as a module-level variable. It is written by the poller thread (\`app/main.py:38\`) and read by the HTTP handler thread without any lock. This is a data race.

## Suggested Fix

Use \`threading.Lock\` or a \`threading.Event\`, store the value in the database, or use an atomic type.

_From code audit in https://github.com/selmer/litterbox/issues/71_"

# Issue 11 - Architecture
gh issue create --repo "$REPO" \
  --title "[Architecture] Long-lived SQLAlchemy session in the poller thread" \
  --body "## Description

\`app/main.py:34\` creates a single \`SessionLocal()\` and passes it to \`LitterboxPoller\`, which keeps it alive across polls. This session may accumulate stale data (SQLAlchemy identity map) and if the DB connection drops mid-session, state can become inconsistent.

## Suggested Fix

Create a new short-lived session per poll cycle inside \`LitterboxPoller.poll()\`.

_From code audit in https://github.com/selmer/litterbox/issues/71_"

# Issue 12 - Architecture
gh issue create --repo "$REPO" \
  --title "[Architecture] N+1 query problem in dashboard endpoint" \
  --body "## Description

\`app/routers/dashboard.py:29-61\` — for each active cat, two separate queries are executed (one for today's visits, one for the last visit). With N cats, this is 2N+3 queries per dashboard request.

## Suggested Fix

Replace with a single JOIN query using \`func.count\`, \`func.sum\`, and a lateral/subquery for the last visit.

_From code audit in https://github.com/selmer/litterbox/issues/71_"

# Issue 13 - Architecture
gh issue create --repo "$REPO" \
  --title "[Architecture] __import__('datetime') hack in production code (app/poller.py)" \
  --body "## Description

\`app/poller.py:143\` uses:
\`\`\`python
started_at=now - __import__('datetime').timedelta(seconds=duration or 0),
\`\`\`
\`timedelta\` is not imported at the top of the file but \`datetime\` is.

## Suggested Fix

Add \`from datetime import datetime, timezone, timedelta\` to imports and remove the \`__import__\` hack.

_From code audit in https://github.com/selmer/litterbox/issues/71_"

# Issue 14 - Architecture
gh issue create --repo "$REPO" \
  --title "[Architecture] DeviceSnapshot and SettingsHistory tables grow forever with no cleanup" \
  --body "## Description

There is no TTL, archival, or cleanup policy. The poller saves a snapshot every \`SNAPSHOT_INTERVAL_SECONDS\` (default 300s = 288/day) and records every settings change. After months of operation this will be a large, never-queried table.

## Suggested Fix

Add a scheduled cleanup job or a migration that adds a retention policy (e.g. keep last 30 days of snapshots).

_From code audit in https://github.com/selmer/litterbox/issues/71_"

# Issue 15 - Architecture
gh issue create --repo "$REPO" \
  --title "[Architecture] SettingsHistory.value has no read/query path" \
  --body "## Description

\`app/models.py:76\` has a comment 'store as string, parse on read' but there is no read/query endpoint for \`SettingsHistory\` anywhere in the codebase. The data is written by \`_record_setting_change\` but never surfaced.

## Suggested Fix

Either expose it via an API endpoint or remove the table to avoid confusion.

_From code audit in https://github.com/selmer/litterbox/issues/71_"

# Issue 16 - Architecture
gh issue create --repo "$REPO" \
  --title "[Architecture] CatPhotoUpload component has no backend storage implementation" \
  --body "## Description

\`frontend/src/components/CatPhotoUpload.jsx\` implements a full crop/compress UI and calls \`onSave(preview)\` with a base64 data URL. However there is no API endpoint for persisting photos, no model field for it, and no backend storage. The \`.gitignore\` mentions \`uploads/cat_photos/\` as if this was planned. This is dead-end UI.

## Suggested Fix

Either implement the backend photo storage or remove the component.

_From code audit in https://github.com/selmer/litterbox/issues/71_"

# Issue 17 - Architecture
gh issue create --repo "$REPO" \
  --title "[Architecture] Dashboard 'today' uses UTC midnight, not user's local time" \
  --body "## Description

\`app/routers/dashboard.py:24\`: \`today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)\` uses UTC midnight. Users in UTC+1 or UTC-5 will see a different 'today' than their local day.

## Suggested Fix

Accept a timezone offset as a query parameter or use the \`time_zone\` from the device config (already in \`tuya-raw.json\`).

_From code audit in https://github.com/selmer/litterbox/issues/71_"

# Issue 18 - Architecture
gh issue create --repo "$REPO" \
  --title "[Architecture] alembic/env.py creates a redundant second engine ignoring pool config" \
  --body "## Description

\`alembic/env.py:61\` instantiates a raw \`create_engine(DATABASE_URL)\` in \`run_migrations_online()\` instead of importing from \`app/database\`. This means the \`pool_pre_ping=True\` and any future pool config from \`database.py\` is not used during migrations, and there are effectively two separate engine objects.

_From code audit in https://github.com/selmer/litterbox/issues/71_"

# Issue 19 - Architecture
gh issue create --repo "$REPO" \
  --title "[Architecture] No offset/cursor pagination on visits endpoint" \
  --body "## Description

\`app/routers/visits.py:31\` supports \`limit\` but no \`offset\` or cursor. The frontend hardcodes \`limit=100\` in the Visits page. Users with many visits cannot page through them and are silently capped at 100.

_From code audit in https://github.com/selmer/litterbox/issues/71_"

# Issue 20 - Architecture
gh issue create --repo "$REPO" \
  --title "[Architecture] Duplicate environment example files (env-example vs .env.example)" \
  --body "## Description

Both \`env-example\` and \`.env.example\` exist in the repo root with the same content (plus \`.env.example\` is also in \`tools/\`).

## Suggested Fix

Consolidate to one canonical example file.

_From code audit in https://github.com/selmer/litterbox/issues/71_"

# Issue 21 - Architecture
gh issue create --repo "$REPO" \
  --title "[Architecture] POLLER_HEALTHY_THRESHOLD_SECONDS is hardcoded and mismatched with POLL_INTERVAL_SECONDS" \
  --body "## Description

\`app/routers/dashboard.py:13\` hardcodes 30 seconds but \`docker-compose.yml:13\` sets \`POLL_INTERVAL_SECONDS=5\`. If the poll interval is changed, the health threshold does not adapt.

## Suggested Fix

Derive this constant from \`POLL_INTERVAL_SECONDS\` (e.g. \`POLL_INTERVAL_SECONDS * 3\`) or make it a configurable env variable.

_From code audit in https://github.com/selmer/litterbox/issues/71_"

# Issue 22 - Architecture
gh issue create --repo "$REPO" \
  --title "[Architecture] _identify_visit_cat passes potentially-None weight causing TypeError" \
  --body "## Description

\`app/poller.py:189\` calls \`identify_cat(weight_kg, ...)\` where \`weight_kg\` could be \`None\` (visits created via \`_handle_visit_complete\` when the weight DP is 0/missing). \`identify_cat\` checks \`if weight_kg <= 0\` but \`None <= 0\` in Python 3 raises a \`TypeError\`.

## Suggested Fix

Add a \`None\` guard in \`_identify_visit_cat\` before passing weight to \`identify_cat\`.

_From code audit in https://github.com/selmer/litterbox/issues/71_"

# Issue 23 - Architecture
gh issue create --repo "$REPO" \
  --title "[Architecture] bfg-1.14.0.jar binary committed to repository" \
  --body "## Description

\`bfg-1.14.0.jar\` (14 MB Java binary) is committed to the repo. Binaries should not live in version control.

## Suggested Fix

Add it to \`.gitignore\` and document the intended BFG usage in the README instead.

_From code audit in https://github.com/selmer/litterbox/issues/71_"

# Issue 24 - Minor
gh issue create --repo "$REPO" \
  --title "[Quality] HTTPException imported inside function bodies instead of at module level" \
  --body "## Description

\`app/routers/visits.py:102,112,128\` imports \`from fastapi import HTTPException\` three times inside individual functions. It should be at the top-level imports.

_From code audit in https://github.com/selmer/litterbox/issues/71_"

# Issue 25 - Minor
gh issue create --repo "$REPO" \
  --title "[Quality] Frontend errors are silently swallowed with no user feedback" \
  --body "## Description

- \`frontend/src/pages/Visits.jsx:27\`: \`handleDelete\` catches errors and only logs to console. The user gets no feedback.
- \`frontend/src/pages/Cats.jsx:84-99\`: \`handleCreate\`/\`handleUpdate\`/\`handleToggleActive\` have no error handling at all. A failed API call will silently leave the UI in a stale state.

## Suggested Fix

Add user-visible error handling (toast notifications, error messages, etc.) for all API calls.

_From code audit in https://github.com/selmer/litterbox/issues/71_"

# Issue 26 - Minor
gh issue create --repo "$REPO" \
  --title "[Quality] Visits with ended_at=NULL not cleaned up on startup after crash" \
  --body "## Description

When \`_handle_weight_update\` runs and \`current_visit is None\`, the visit is committed to the DB immediately with \`ended_at=None\`. If the app crashes between the weight event and the completion event, the DB will have a perpetually-open visit with no end time.

## Suggested Fix

Add a startup cleanup query that closes any visits with \`ended_at IS NULL\` that are older than \`VISIT_TIMEOUT_SECONDS\`.

_From code audit in https://github.com/selmer/litterbox/issues/71_"

# Issue 27 - Minor
gh issue create --repo "$REPO" \
  --title "[Quality] No database indexes on Visit.started_at or Visit.cat_id" \
  --body "## Description

\`app/models.py:46-47\` — the \`started_at\` and \`cat_id\` columns are heavily filtered in dashboard and visit queries but have no index defined.

## Suggested Fix

Add \`index=True\` to these columns in the model and create a corresponding migration.

_From code audit in https://github.com/selmer/litterbox/issues/71_"

echo "Done! All 27 issues created."
