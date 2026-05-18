# UI Foundation Polish Pass

Priority: P1

Implementation scope:
Frontend shared UI foundation. This spec creates reusable polish primitives and cleans up styling patterns that currently make screens drift apart.

## Summary

- Establish shared UI primitives for recurring layout, state, and action patterns.
- Reduce high-use inline styles in pages and components.
- Make buttons, badges, modals, empty states, and page headers feel consistent across Dashboard, Visits, and Cats.
- Keep the existing visual direction and theme tokens.

## Key Changes

- Add or consolidate small reusable primitives:
  - `PageHeader` for title, subtitle/date, and right-side status/action content.
  - `EmptyState` for compact empty/loading/error surfaces.
  - `StatusBadge` for auto/manual/unidentified/inactive/status labels.
  - `ModalShell` or shared modal classes for consistent title, copy, actions, and width.
  - `Button` or stricter button class variants if the codebase stays CSS-first.
- Move repeated inline styles into named classes where they are used across screens.
- Normalize action hierarchy:
  - primary actions for creation or confirmation
  - secondary actions for navigation/cancel
  - danger treatment for destructive confirmation only
- Keep card usage restrained: cards for actual surfaces and repeated items, not nested decorative wrappers.
- Keep motion subtle: hover color/shadow changes are fine; avoid bouncy or page-level animations.

## Visual Details

- Preserve existing spacing tokens and add only small missing utility classes when needed.
- Use `8px` to `18px` radii according to existing components; avoid adding larger pill-like surfaces unless the component is explicitly a badge or status pill.
- Empty states should be compact and operational, with optional action buttons only when there is an obvious next step.
- Modal copy should be concise and task-focused.
- Toasts should remain short-lived feedback, not the primary place where users recover from page errors.

## Acceptance Criteria

- Dashboard, Visits, and Cats use the same page header and empty-state language patterns.
- Common badges share one implementation or one CSS system.
- Repeated inline layout styles are replaced with classes or primitives where doing so reduces duplication.
- Light and dark themes still use existing tokens and render without one-off hardcoded theme exceptions beyond necessary semantic colors.
- No backend or API changes are introduced.

## Verification Plan

- Run frontend tests for affected components and pages.
- Manually verify Dashboard, Visits, Cats, add visit modal, reassign modal, cat form, loading states, empty states, and toasts.
- Check desktop, tablet, and mobile widths in both themes.
- Confirm no text overlaps and no modal exceeds the viewport on mobile.

## Assumptions

- This pass may add small frontend components, but should not redesign individual screen flows.
- Screen-specific redesign belongs to specs `022`, `023`, and `024`.
- Accessibility work remains light-touch: keep visible focus behavior and reasonable hit targets.
