# Navigation and Icon System

Priority: P1

Implementation scope:
Frontend navigation and iconography. This spec replaces placeholder glyph and emoji-based UI markers with a consistent icon system and refines the app shell.

## Summary

- Replace abstract glyphs and UI emoji with a consistent icon set.
- Polish the sidebar, mobile header/navigation behavior, app mark, and theme toggle.
- Preserve the current app routes and theme persistence.

## Key Changes

- Add a single icon source, preferably `lucide-react`, if it fits the existing frontend dependency approach.
- Replace navigation glyphs:
  - Dashboard: layout/grid icon.
  - Visits: calendar, clipboard, or list icon.
  - Cats: cat or identity/tag icon.
- Replace summary metric glyphs in the cat card with matching line icons.
- Keep cat photos as real images; use a designed fallback avatar instead of raw emoji when no photo exists.
- Refine the theme toggle:
  - desktop: compact utility control in the sidebar footer
  - mobile: icon-only or concise control in the mobile header
  - copy and aria label continue to reflect the target theme
- Keep active navigation state clear but quiet in both themes.

## Visual Details

- Icons should share size, stroke width, and alignment.
- Do not mix emoji, abstract Unicode glyphs, and icon-library symbols in primary UI controls.
- The app mark can remain cat-themed, but should look intentional and consistent with the icon system.
- Mobile navigation should avoid horizontal clutter and preserve clear route labels or familiar icon-label pairing.

## Acceptance Criteria

- Sidebar and mobile navigation no longer use placeholder glyphs.
- Cat summary metrics use meaningful icons from the same system.
- Fallback cat avatar looks intentional in light and dark themes.
- Theme toggle remains functional and persists the selected theme in local storage.
- Existing routes remain unchanged: Dashboard, Visits, and Cats.

## Verification Plan

- Run frontend tests that cover app shell, routing, and theme toggle behavior.
- Manually verify active nav states on each route.
- Check desktop and mobile layouts in both themes.
- Confirm no icon shifts layout when labels or active states change.

## Assumptions

- If adding `lucide-react` is not practical, use one existing icon source consistently instead.
- This spec does not redesign the Visits or Cats page content beyond icons and navigation shell polish.
