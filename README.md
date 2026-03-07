# litterbox

Attempting to connect to a viervoeter Litterbox

## Running the test suite

Install dependencies (requires Python 3.11+):

```bash
pip install -r requirements.txt -r requirements-test.txt
```

Run all tests:

```bash
pytest
```

Useful flags:

```bash
pytest -v                                  # verbose output
pytest tests/test_poller.py -v             # single file
pytest tests/test_api_dashboard.py -v      # dashboard tests only
pytest -x                                  # stop on first failure
```

No real device or database is needed — tests use an in-memory SQLite database
and mock the Tuya cloud entirely.

### Test files

| File | What it covers |
|---|---|
| `tests/test_health.py` | `/health` smoke test |
| `tests/test_api_cats.py` | `/cats` — create, list, get, update |
| `tests/test_api_visits.py` | `/visits` — CRUD, filtering, weight history |
| `tests/test_api_cleaning_cycles.py` | `/cleaning-cycles` — listing, ordering, limits |
| `tests/test_api_dashboard.py` | `/dashboard` — aggregations, poller health |
| `tests/test_poller.py` | `LitterboxPoller` state machine — weight events, visit lifecycle, timeouts, cleaning cycles |
| `tests/test_cat_identifier.py` | `identify_cat` and `update_reference_weight` pure-function tests |