# Pydantic v2 Config Deprecation Cleanup

Priority: P2

Problem:
Backend tests emit Pydantic v2 deprecation warnings because response schemas in `app/schemas.py` still use class-based `Config` for `from_attributes`.

Proposed behavior:

- Replace class-based `Config` with `model_config = ConfigDict(from_attributes=True)`.
- Keep API response shapes unchanged.
- Do not change validation rules or database behavior.

Acceptance criteria:

- `CatOut`, `VisitOut`, and `CleaningCycleOut` use Pydantic v2 `ConfigDict`.
- Backend tests pass without the three Pydantic `Config` deprecation warnings.

Verification:

- Run `python3 -m pytest tests/ -q`.
