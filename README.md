# litterbox

Attempting to connect to a viervoeter Litterbox

## Running the test suite

### Prerequisites

Install the main dependencies and the test-only extras:

```bash
pip install -r requirements.txt -r requirements-test.txt
```

The test suite uses an in-memory SQLite database and mocks out the Tuya cloud
connection, so **no real device or database is required** to run tests.

### Run all tests

```bash
pytest
```

### Run with verbose output

```bash
pytest -v
```

### Run a specific test file

```bash
pytest tests/test_api_cats.py -v
pytest tests/test_poller.py -v
```

### Run a specific test

```bash
pytest tests/test_poller.py::TestHandleWeightUpdate::test_creates_new_visit_on_first_weight -v
```

### Test files

| File | What it covers |
|---|---|
| `tests/test_cat_identifier.py` | `identify_cat` and `update_reference_weight` pure logic |
| `tests/test_health.py` | `/health` endpoint |
| `tests/test_api_cats.py` | `/cats` CRUD endpoints |
| `tests/test_api_visits.py` | `/visits` CRUD + weight history endpoints |
| `tests/test_api_cleaning_cycles.py` | `/cleaning-cycles` listing endpoint |
| `tests/test_api_dashboard.py` | `/dashboard` aggregation endpoint |
| `tests/test_poller.py` | `LitterboxPoller` state-machine logic |

---

## Tests that need owner input

The following areas have placeholder assumptions in the tests. Each test file
has a docstring explaining the uncertainty, but a summary is below.

### 1. Real device DP values (`tests/test_poller.py`)

The poller tests assume:
- `cat_weight` is reported in **grams** as an integer (e.g. `4200` → 4.2 kg)
- `excretion_time_day` is reported in **seconds** as an integer
- `smart_clean` is `True` when a cleaning cycle starts and `False` when it ends

If the real Tuya device behaves differently, update `tests/test_poller.py`
and possibly the conversion logic in `poller.py`.

### 2. Cat reference weights (`tests/test_api_cats.py`, `tests/test_poller.py`)

Tests use placeholder cats named "Luna" (4.0 kg) and "Mochi" (6.0 kg).
Once real cats are registered, you may want to add regression tests with
their actual weights to ensure the identification threshold (currently 0.5 kg)
keeps working correctly.

### 3. Poller health threshold (`tests/test_api_dashboard.py`)

`POLLER_HEALTHY_THRESHOLD_SECONDS` is set to **30 seconds** in
`app/routers/dashboard.py`, but the default polling interval is **300 seconds**.
This means the dashboard will show the poller as unhealthy for most of each
poll cycle. Confirm whether this is intentional, or if the threshold should
be raised to something like 600 seconds.

### 4. Unidentified visit handling (`tests/test_api_dashboard.py`)

The dashboard counts unidentified visits where `ended_at IS NOT NULL`. Visits
that are still in progress (no `ended_at`) are excluded. Confirm this matches
the expected dashboard behaviour.

### 5. Reference weight smoothing factor (`tests/test_cat_identifier.py`)

`update_reference_weight` uses a default smoothing of `0.1`. If you observe
rapid weight fluctuations with the real device (e.g. due to scale jitter),
you may want to tune this value and add a regression test for the chosen value.