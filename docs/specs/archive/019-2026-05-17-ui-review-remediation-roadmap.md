# UI Review Remediation Roadmap

Priority: P1

Implementation scope:
Frontend specification roadmap only. This spec coordinates follow-up UI remediation specs and does not directly authorize frontend code changes by itself.

## Summary

- Split the UI review follow-up into small implementation slices instead of one large redesign.
- Preserve the current Light Professional and Dark Elegant direction.
- Bring the secondary screens up to the same design quality as the dashboard.
- Keep accessibility light-touch: retain sensible focus states and usable controls, but do not treat this as a full WCAG audit.

## Direction

The app should feel like a quiet operational health monitor: compact, trustworthy, and warm without becoming playful or decorative. The dashboard is the reference direction. Visits, Cats, modals, empty states, and action flows should be brought into that same system.

Design principles:

- Prefer operational clarity over visual novelty.
- Keep theme decisions in tokens and CSS classes.
- Use consistent icons, spacing, card treatment, labels, and action hierarchy.
- Avoid large marketing-style layouts, decorative illustrations, and nested cards.
- Treat dark mode as a first-class theme, not as an inverted afterthought.

## Implementation Order

1. Implement `020` first to establish reusable UI primitives and polish rules.
2. Implement `021` next to replace placeholder iconography and refine navigation.
3. Implement `022` for the Visits screen, because it has the highest usability payoff.
4. Implement `023` for the Cats screen, reusing primitives from `020`.
5. Implement `024` last for chart/dashboard refinements after the foundation is stable.

## Spec Boundaries

- `020` owns shared primitives, token cleanup, inline-style cleanup, empty states, modals, buttons, and badges.
- `021` owns navigation, app branding, icon system, and theme toggle treatment.
- `022` owns visit filtering, visit table/mobile layout, row actions, reassign/delete flows, and pagination polish.
- `023` owns cat management layout, profile rows/cards, photo/avatar consistency, and active/inactive states.
- `024` owns chart readability, range persistence, dashboard empty states, and final dashboard theme polish.

## Acceptance Criteria

- Specs `020` through `024` can be implemented independently in order.
- Each spec has one primary owner area and avoids duplicating work from other specs.
- No backend changes are required for this remediation roadmap.
- Later UI changes remain visually consistent in both `light-professional` and `dark-elegant`.

## Verification Plan

- Before implementing each spec, confirm no newer spec supersedes its scope.
- After each implementation slice, run the relevant frontend tests.
- Perform visual QA for desktop, tablet, and mobile in both themes.
- Confirm the dashboard, visits, cats, modals, empty states, theme toggle, and poller status still function after each slice.

## Assumptions

- The existing React/Vite frontend structure remains in place.
- The existing theme names remain `light-professional` and `dark-elegant`.
- The remediation is product/UI polish, not a backend feature pass.
- The current dashboard direction remains the visual baseline.
