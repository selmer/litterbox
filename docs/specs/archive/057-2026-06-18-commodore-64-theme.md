# Commodore 64 Theme

Priority: P2

Implementation scope:
Frontend theme tokens, font loading, theme selection UI, translations, and visual verification. This spec adds an optional Commodore 64 inspired theme using period-appropriate colors and typography while preserving app usability.

## Summary

- Add a third selectable theme inspired by Commodore 64 visuals.
- Use C64-style blue tones, light cyan text, and pixel/monospace typography.
- Keep the theme usable for operational monitoring, forms, tables, charts, and modals.
- Preserve the existing light-professional and dark-elegant themes.

## Problem

The app currently supports two polished operational themes:

- `light-professional`
- `dark-elegant`

A Commodore 64 inspired theme would add a playful, nostalgic mode for a self-hosted household device dashboard. The risk is that a literal retro treatment can harm readability, contrast, and dense data scanning if applied too aggressively. The theme should evoke the C64 without making the app feel broken or hard to operate.

## Current Behavior

- `frontend/src/App.jsx` stores one active theme in local storage under `cat-health-monitor-theme`.
- The theme toggle switches between light and dark only.
- `frontend/src/index.css` defines theme tokens for `[data-theme="light-professional"]` and `[data-theme="dark-elegant"]`.
- Component styles mostly consume CSS variables, making a token-based third theme practical.
- `frontend/src/i18n/translations.js` contains theme labels and switch copy.

## Proposed Behavior

Add a new theme id:

- `commodore-64`

The theme should be selectable from the app shell. Because there will be three themes, replace the binary light/dark toggle with a compact theme selector or menu.

Theme direction:

- Backgrounds:
  - deep C64 blue for the app background.
  - slightly lighter blue for cards/sidebar.
  - strong but not harsh border blue.
- Text:
  - light cyan or pale blue for primary text.
  - muted blue/cyan for secondary text.
- Accent:
  - C64 cyan or light blue for selected states and primary actions.
  - use semantic warning/danger/success colors that remain readable on blue.
- Typography:
  - use a C64-style pixel or monospace font where available.
  - if bundling a font, keep it local and license-compatible.
  - if no bundled font is added, use a pixel-style fallback stack only where it renders well.
- UI treatment:
  - slightly sharper visual feel is allowed, but do not break existing spacing or layout.
  - avoid novelty effects that reduce clarity, such as scanlines over text, blinking text, or excessive text shadows.

## Implementation Notes

- Add a new constant in `frontend/src/App.jsx`, for example `C64_THEME = 'commodore-64'`.
- Replace binary theme toggle logic with theme cycling or a small selector:
  - Light
  - Dark
  - C64
- Update translations for theme labels in English and Dutch.
- Add `[data-theme="commodore-64"]` tokens in `frontend/src/index.css`.
- Review theme-specific overrides in `frontend/src/App.css`; add C64 overrides only where token changes are insufficient.
- Update chart colors so multiple cats remain distinct on the C64 blue background.
- Consider a local font asset only if the license is clear and the file size is reasonable.
- Respect `prefers-reduced-motion`; do not add retro animations.

Suggested initial palette, subject to visual tuning:

- app background: `#40318D` or `#352879`
- card/sidebar: `#50459B`
- elevated card: `#5B50A6`
- primary text: `#A7FFFF`
- secondary text: `#7FD6FF`
- muted text: `#6CA6D9`
- accent: `#7CFFFF`
- accent soft: rgba cyan over blue
- border: `#7869C4`

## Non-Goals

- Do not replace the existing light or dark themes.
- Do not make C64 the default theme.
- Do not change backend APIs or data models.
- Do not add sound effects, animations, scanline overlays, CRT curvature, or decorative retro noise.
- Do not sacrifice table readability or form usability for nostalgia.
- Do not fetch fonts from a CDN at runtime.

## Acceptance Criteria

- A third theme, `commodore-64`, can be selected from the app shell.
- The selected C64 theme persists in local storage and restores on reload.
- Light and dark themes still work exactly as before.
- English and Dutch labels exist for the new theme option.
- Dashboard, Visits, Cats, Cat detail, Admin, Diagnostics, modals, toasts, badges, alerts, and charts render legibly in the C64 theme.
- Primary, secondary, warning, danger, success, muted, and active states remain visually distinguishable.
- The C64 theme does not introduce layout shifts or text overflow.
- No remote font dependency is required at runtime.

## Verification Plan

- Add/update frontend tests for theme selection and persistence.
- Run `npm run lint` in `frontend/`.
- Run `npm test` in `frontend/`.
- Manually verify all major screens in the C64 theme:
  - Dashboard with chart, cat cards, alerts, and health signals.
  - Visits summary and details modes.
  - Cats list and Cat detail event history.
  - Admin backup/restore states.
  - Diagnostics payload-heavy states.
  - Add/edit/delete modals.
- Check mobile and desktop widths.
- Check that text remains readable against blue surfaces.

## Rollback Notes

No backend or data migration is required. Rolling back removes the `commodore-64` theme option and its CSS tokens. Existing stored values of `commodore-64` should fall back to `light-professional` after rollback or during implementation if the theme id is unknown.
