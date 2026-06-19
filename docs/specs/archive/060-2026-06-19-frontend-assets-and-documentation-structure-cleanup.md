# Frontend Assets and Documentation Structure Cleanup

Priority: P2

Implementation scope:
Frontend starter assets, static icons, colocated tests, frontend docs, and documentation layout. This spec removes unused starter files and clarifies where frontend documentation belongs without changing UI behavior.

## Summary

- Remove unused Vite/React starter assets.
- Keep the existing app icon system unless a separate UI icon migration is requested.
- Decide whether `frontend/docs/README.md` belongs in frontend-local docs or central project docs.
- Keep colocated frontend tests unless there is a strong reason to move them.

## Problem

The frontend has evolved into a real application, but a few starter artifacts and documentation placement choices still look like scaffolding. These files add visual noise and make it less clear which assets are actually part of the product.

Observed examples:

- `frontend/public/vite.svg`
- `frontend/src/assets/react.svg`
- `frontend/public/cat.svg`
- `frontend/docs/README.md`
- Frontend test files are colocated with source files, which is acceptable but should be documented as intentional if retained.

## Current Behavior

- The application uses `frontend/src/components/Icon.jsx` for inline SVG icons.
- Searches show no active imports of `frontend/src/assets/react.svg` or `frontend/public/vite.svg`.
- `frontend/public/cat.svg` was confirmed unused; `frontend/index.html` uses an inline data-SVG favicon instead.
- Vite config uses Vitest with `frontend/src/test-setup.js`.
- Tests are colocated under `frontend/src/pages/*.test.jsx` and `frontend/src/components/*.test.jsx`.

## Proposed Behavior

Remove unused starter assets:

- Delete `frontend/src/assets/react.svg`.
- Delete `frontend/public/vite.svg`.

Assess `frontend/public/cat.svg`:

- Keep it if referenced by `frontend/index.html`, manifest metadata, tests, CSS, or expected static URLs.
- Delete it if it is unused and fully replaced by `Icon.jsx` or uploaded cat photos.

Clarify test placement:

- Keep colocated frontend tests where they are.
- Optionally add a short note in `frontend/docs/README.md` or README that frontend tests live next to the pages/components they cover.
- Do not move tests into a separate spec folder; specs and tests serve different purposes.

Clarify frontend documentation:

- If `frontend/docs/README.md` is frontend-specific and useful, keep it.
- If it duplicates root README or general docs, merge useful content into:
  - `README.md`, or
  - `docs/frontend.md`
- Remove `frontend/docs/README.md` only after useful content is migrated or proven obsolete.

Optional later improvement:

- Consider replacing custom inline icons with `lucide-react` in a separate UI-focused spec. Do not mix that migration into this cleanup unless explicitly requested.

## Implementation Notes

- Before deleting static assets, run a repository search for each filename.
- Keep cleanup behavior-neutral: no visual redesign, no theme changes, no dependency changes.
- If `frontend/public/cat.svg` is used as a browser-visible asset, update any references before renaming/removing.
- If deleting `frontend/src/assets/` leaves the directory empty, remove the directory from git.
- Do not move frontend tests as part of this cleanup.

## Non-Goals

- Do not redesign navigation or icons.
- Do not introduce `lucide-react` or another icon library.
- Do not reorganize all frontend source directories.
- Do not change app routes, API calls, theme behavior, or localization behavior.
- Do not move colocated tests unless a separate test-organization spec is approved.

## Acceptance Criteria

- `frontend/src/assets/react.svg` is removed if unused.
- `frontend/public/vite.svg` is removed if unused.
- `frontend/public/cat.svg` is removed as unused; `frontend/index.html` keeps the inline favicon.
- No source file, CSS file, test, or HTML file references deleted assets.
- Frontend tests remain discoverable by Vitest.
- Frontend documentation has one clear home:
  - retained under `frontend/docs/` for frontend-only notes, or
  - migrated to central `docs/` if project-wide.
- No visible UI behavior changes are introduced.

## Verification Plan

- Run:

```bash
rg -n 'react\.svg|vite\.svg|cat\.svg' frontend README.md docs
```

- Confirm no deleted asset is referenced.
- Run frontend checks:

```bash
cd frontend
npm run lint
npm test
npm run build
```

- If `cat.svg` is kept, manually confirm why it is kept in the implementation notes or README.
- If `frontend/docs/README.md` is changed or removed, manually verify README/doc links.

## Rollback Notes

Rollback is a normal git revert. If a deleted static asset turns out to be needed by an external bookmark, browser cache, or deployed static URL, restore it under `frontend/public/` and document the dependency.
