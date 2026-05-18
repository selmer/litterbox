# 038 - OpenAPI and Swagger Documentation

## Summary
Document and verify the OpenAPI/Swagger support that FastAPI already provides. This is not a new Swagger generator. The goal is to make the existing API docs discoverable and covered by a light smoke test.

## Key Changes
- Document the existing FastAPI docs endpoints:
  - Swagger UI: `/docs`
  - ReDoc: `/redoc`
  - OpenAPI JSON: `/openapi.json`
- Add README or docs guidance for using these endpoints locally and on the NAS.
- Add a smoke test that confirms `/openapi.json` is available and includes core routes.

## Public Interfaces
- No new runtime API shape.
- Existing FastAPI documentation endpoints become explicitly documented as supported developer/operator affordances.

## Test Plan
- `GET /openapi.json` returns 200.
- OpenAPI JSON includes paths for `/cats`, `/visits`, `/dashboard`, and `/display/summary`.
- Documentation references are accurate for the deployed app port.

## Assumptions
- FastAPI's built-in Swagger UI is sufficient for now.
- No static OpenAPI artifact needs to be committed in this pass.
