# Modal Accessibility and Ergonomics

Priority: P1

Implementation scope:
Frontend shared modal primitive and all modal consumers. This spec makes modals more accessible, easier to close, and safer for keyboard users.

## Summary

- Add proper dialog semantics to the shared modal shell.
- Add a visible close control.
- Manage focus when modals open and close.
- Preserve existing modal workflows and copy.

## Problem

The shared `ModalShell` gives the app consistent modal visuals, but it is currently minimal:

- no `role="dialog"`.
- no `aria-modal`.
- no labelled title id.
- no visible close button.
- no focus trap or focus restoration.
- Escape-key behavior is not defined.

This affects workflows such as editing visits, deleting visits, and adding manual visits. These flows are important, sometimes destructive, and should be comfortable for keyboard and assistive technology users.

## Current Behavior

- `frontend/src/components/ui.jsx` exports `ModalShell`.
- The overlay closes when clicked.
- The modal content stops propagation.
- Consumers pass title, optional description, children, and `onClose`.
- Modal actions are implemented inside each consumer.

## Proposed Behavior

Upgrade `ModalShell` to support:

- `role="dialog"`.
- `aria-modal="true"`.
- `aria-labelledby` pointing to the modal title.
- `aria-describedby` when description exists.
- visible close button in the top-right.
- Escape key closes the modal.
- focus moves into the modal when opened.
- focus returns to the previously focused element when closed.
- tab focus remains inside the modal while open.

The visual treatment should stay quiet and consistent with the app:

- close button is an icon button with accessible label.
- modal width remains constrained.
- mobile modals fit within the viewport and scroll internally if needed.

## Implementation Notes

- Update `ModalShell` in `frontend/src/components/ui.jsx`.
- Add CSS in `frontend/src/App.css` for:
  - modal header/title row if needed.
  - close icon button.
  - max-height and overflow behavior.
- Use existing `Icon` component if it has a close icon; add one only if needed.
- Avoid introducing a large dialog dependency.
- Review all modal consumers:
  - Dashboard add manual visit modal.
  - Visits edit visit modal.
  - Visits delete confirmation modal.
  - Cat photo upload/crop modals if they use shared modal styles.
- Confirm overlay click still works unless a consumer explicitly disables it in a later spec.

## Non-Goals

- Do not redesign modal content.
- Do not change form validation logic.
- Do not change API mutations.
- Do not add nested modals.
- Do not replace all forms with modals.

## Acceptance Criteria

- Every `ModalShell` instance has dialog semantics.
- Modal title is exposed as the accessible name.
- Description is exposed when present.
- A visible close button is present and keyboard focusable.
- Escape closes the modal.
- Focus is moved into the modal on open.
- Focus returns to the trigger after close when possible.
- Tabbing cycles within the modal while open.
- Existing modal tests pass after updates.

## Verification Plan

- Add tests for `ModalShell` behavior:
  - role/name.
  - close button.
  - Escape close.
  - focus placement and restoration where practical in jsdom.
- Update page tests that query modal titles/actions if required.
- Run `npm run lint` in `frontend/`.
- Run `npm test` in `frontend/`.
- Manual keyboard check:
  - open modal.
  - tab through controls.
  - press Escape.
  - verify focus returns.

## Rollback Notes

No backend or data change is involved. Rollback restores the previous modal shell behavior.
