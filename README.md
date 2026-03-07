# litterbox

Attempting to connect to a viervoeter Litterbox

## Running the test suite

Install dependencies (pytest and httpx are included in `requirements.txt`):

```bash
pip install -r requirements.txt
```

Run all tests:

```bash
python3 -m pytest tests/ -v
```

Run a specific test file:

```bash
python3 -m pytest tests/test_api_cats.py -v
python3 -m pytest tests/test_poller.py -v
```

Tests use an in-memory SQLite database and mock out the Tuya cloud connection, so no real device or credentials are needed.

The test suite is also run automatically by `deploy.sh` before every deploy. If any test fails, the deploy aborts.

### Test files

| File | What it covers |
|---|---|
| `tests/test_cat_identifier.py` | `identify_cat()` and `update_reference_weight()` pure-logic tests |
| `tests/test_health.py` | `GET /health` endpoint |
| `tests/test_api_cats.py` | Cats CRUD (`POST /cats`, `GET /cats`, `GET /cats/{id}`, `PATCH /cats/{id}`) |
| `tests/test_api_visits.py` | Visits CRUD + weight history endpoint |
| `tests/test_api_cleaning_cycles.py` | `GET /cleaning-cycles` listing |
| `tests/test_api_dashboard.py` | Dashboard aggregation (visits today, cleaning cycles, poller health) |
| `tests/test_poller.py` | `LitterboxPoller` internal logic (visit creation, timeout, cleaning cycles, snapshots, settings) |

## Cleaning git history with BFG

[BFG Repo Cleaner](https://rtyley.github.io/bfg-repo-cleaner/) is a faster alternative to `git filter-branch` for removing large files or sensitive data from git history.

### Setup

Download the BFG jar (do **not** commit it to the repository):

```bash
curl -L -o bfg.jar https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar
```

Requires Java 8+. Check with `java -version`.

### Common usage

**Remove a committed file from all history:**

```bash
# First, delete the file from the latest commit if it's still there
git rm --cached path/to/file && git commit -m "Remove file"

# Then rewrite history
java -jar bfg.jar --delete-files filename.ext

# Clean up and force-push
git reflog expire --expire=now --all && git gc --prune=now --aggressive
git push --force
```

**Remove files larger than a given size:**

```bash
java -jar bfg.jar --strip-blobs-bigger-than 10M
```

> **Note:** Always take a full backup (`git clone --mirror`) before rewriting history.
> Coordinate with all collaborators — everyone must re-clone after a force-push.

### Areas that need your input for tests

The following cannot be fully covered without real-world data or your specific setup:

1. **Tuya cloud integration** — `LitterboxPoller.poll()` and `_init_cloud()` require live Tuya API credentials (`TUYA_DEVICE_ID`, `TUYA_API_KEY`, `TUYA_API_SECRET`) and a connected device. These are mocked in the current test suite. If you want end-to-end polling tests, provide credentials in a `.env` file and write integration tests tagged with `@pytest.mark.integration`.

2. **Cat identification threshold** — `IDENTIFICATION_THRESHOLD_KG` is set to `0.5 kg`. If your cats have very similar weights, this threshold may need tightening and the corresponding tests in `test_cat_identifier.py` updated with real weight values.

3. **Reference weight smoothing** — The exponential moving-average smoothing factor (`0.1`) controls how quickly a cat's reference weight adapts. Tests verify the math, but the right value depends on your cats' weight patterns.

4. **Visit timeout** — `VISIT_TIMEOUT_SECONDS` (300 s) is a fallback for when the device doesn't send a completion event. If your device behaves differently, this constant and the related poller tests may need adjustment.

5. **Frontend components** — The React components in `frontend/src/` have no automated tests. If you want component or end-to-end browser tests (e.g. with Playwright or Vitest), let me know what behaviour you want covered.
