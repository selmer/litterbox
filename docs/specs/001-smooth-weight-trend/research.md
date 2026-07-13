# Research: Smooth Weight Trend

## Decision: Use presentation-only client-side smoothing

**Rationale**: The existing `GET /visits/weight-history` endpoint already returns ordered original measurements grouped by active cat, excluding ignored weights by default. The user's complaint is that the visible graph looks like a rollercoaster, not that stored data or API responses are wrong. Keeping smoothing in the chart preserves historical measurements, avoids a migration, and avoids contract churn for other clients.

**Alternatives considered**:

- Backend-derived `smoothed_weight_kg` field: rejected for this feature because it would expand the API contract without clear need and would require backend route tests for derived display data.
- Persisted trend table or cached trend values: rejected because the trend is a presentation concern and stored historical measurements must remain the source of truth.
- Mutating stored visit weights: rejected because it violates the specification requirement to preserve existing weight history.

## Decision: Smooth per cat before merging chart rows

**Rationale**: The chart currently merges points by timestamp and visit id after iterating each cat's `data`. Smoothing must be scoped per cat to avoid blending different cats and to preserve the existing multi-cat legend behavior. Per-cat smoothing directly satisfies FR-007.

**Alternatives considered**:

- Smooth the merged chart rows: rejected because sparse rows for multiple cats can introduce nulls and accidental cross-cat influence.
- Show only one selected cat: rejected because the current dashboard shows all active cats and this feature does not request changing chart scope.

## Decision: Keep original measurements in tooltip context

**Rationale**: The spec requires original recorded measurements to remain inspectable. The chart can draw the smoothed value while retaining raw `weight_kg`, visit id, timestamp, and confidence context in each plotted point. Tooltip text should make the recorded value available when the plotted value differs.

**Alternatives considered**:

- Replace raw values everywhere with smoothed values: rejected because it hides what the litterbox recorded.
- Add a separate raw line for every cat: rejected for default display because it would reintroduce visual noise; it can be reconsidered later as an optional mode.

## Decision: Treat fewer than three usable measurements as unsmoothed

**Rationale**: One or two points do not support a reliable trend. Showing the available recorded measurements without smoothing satisfies the sparse-data requirement and avoids implying certainty.

**Alternatives considered**:

- Hide the chart for fewer than three points: rejected because users still benefit from seeing available measurements.
- Extrapolate or interpolate missing points: rejected because it creates visual certainty not present in the data.

## Decision: Do not add a new dependency

**Rationale**: The required smoothing can be expressed with simple deterministic frontend logic and existing Recharts rendering. A new dependency would add audit and maintenance surface without reducing meaningful complexity.

**Alternatives considered**:

- Chart/statistics smoothing library: rejected because the problem scope is narrow and existing tests can cover the expected behavior.

## Decision: Verification focuses on chart data transformation

**Rationale**: Existing tests mock Recharts and inspect the data passed into the chart, which is the right boundary for proving smoother values, preserved raw context, sorted points, and sparse-data behavior without browser pixel tests.

**Alternatives considered**:

- End-to-end browser screenshot verification: rejected for planning as unnecessarily broad for a deterministic chart-data transformation, though manual visual review remains useful.
