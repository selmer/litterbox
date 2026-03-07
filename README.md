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

### Areas that need your input for tests

The following cannot be fully covered without real-world data or your specific setup:

1. **Tuya cloud integration** — `LitterboxPoller.poll()` and `_init_cloud()` require live Tuya API credentials (`TUYA_DEVICE_ID`, `TUYA_API_KEY`, `TUYA_API_SECRET`) and a connected device. These are mocked in the current test suite. If you want end-to-end polling tests, provide credentials in a `.env` file and write integration tests tagged with `@pytest.mark.integration`.

2. **Cat identification threshold** — `IDENTIFICATION_THRESHOLD_KG` is set to `0.5 kg`. If your cats have very similar weights, this threshold may need tightening and the corresponding tests in `test_cat_identifier.py` updated with real weight values.

3. **Reference weight smoothing** — The exponential moving-average smoothing factor (`0.1`) controls how quickly a cat's reference weight adapts. Tests verify the math, but the right value depends on your cats' weight patterns.

4. **Visit timeout** — `VISIT_TIMEOUT_SECONDS` (300 s) is a fallback for when the device doesn't send a completion event. If your device behaves differently, this constant and the related poller tests may need adjustment.

5. **Frontend components** — The React components in `frontend/src/` have no automated tests. If you want component or end-to-end browser tests (e.g. with Playwright or Vitest), let me know what behaviour you want covered.
