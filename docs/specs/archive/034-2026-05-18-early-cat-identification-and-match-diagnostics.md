# 034 - Early Cat Identification and Match Diagnostics

## Summary

Identify a visit as soon as the first reliable `cat_weight` is seen when one cat clearly matches. Keep the global `0.5 kg` threshold unchanged, and add diagnostics so unidentified decisions can be inspected after the fact.

## Problem

A visit can remain visibly unidentified while it is still open, even when the observed weight is clearly consistent with a known cat. For example, Plurk can have several identified weights around `3.78-3.86 kg`, while a later `3.83 kg` open visit appears as `Unknown cat` until completion logic runs.

## Proposed Behavior

- On a new nonzero `cat_weight`, create the visit and immediately attempt cat identification.
- Assign the cat immediately only when exactly one active cat is within the existing threshold.
- If no reference-weight match exists, try a conservative recent-baseline fallback using recent identified visit weights.
- Leave the visit unidentified when matching is ambiguous or unsupported by enough data.
- Update `reference_weight_kg` only when the visit closes, not at early assignment time.
- Record an `identification_attempt` diagnostic with observed weight, candidates, strategy, selected cat, and reason.

## Acceptance Criteria

- A clear Plurk-like `3.830 kg` weight can be assigned at visit start when Plurk is the only plausible match.
- Ambiguous matches remain unidentified.
- Recent-baseline fallback only assigns when a single cat clearly matches.
- The visit diagnostics endpoint explains both assigned and unidentified decisions.
- Reference weights are not updated twice for a single visit.

## Verification Plan

- Unit tests for single, out-of-threshold, and ambiguous reference matching.
- Poller tests for early assignment, delayed reference updates, diagnostics, baseline fallback, and ambiguous fallback rejection.
- Manual API check: a clear in-progress visit appears with the matched cat in `GET /visits` before duration completion.
