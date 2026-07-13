# Contract: Weight Chart Display

## Existing API Contract

The implementation must continue consuming the existing `GET /visits/weight-history` contract without requiring backend changes.

Expected response shape:

```json
[
  {
    "cat_id": 1,
    "cat_name": "Mochi",
    "data": [
      {
        "timestamp": "2026-07-01T10:00:00Z",
        "weight_kg": 4.2,
        "visit_id": 101,
        "weight_confidence": "normal"
      }
    ]
  }
]
```

Compatibility requirements:

- `weight_kg` remains the original recorded value.
- Existing request parameters remain unchanged: `from_date`, `to_date`, and `cat_id`.
- Ignored weights remain excluded by default through the existing endpoint behavior.
- No new required response fields are introduced for this feature.

## UI Data Contract

The chart may derive presentation-only fields before passing rows to Recharts.

Each rendered row for a cat series must retain:

- The chronological timestamp used by the x-axis.
- The displayed smoothed weight value used by the line.
- The original recorded weight value for tooltip/context.
- The visit id for tooltip/context.

Behavioral contract:

- Same-cat measurements may influence only that cat's displayed trend.
- Cats with fewer than three usable measurements render without smoothing.
- The graph must not add invented visits or timestamps.
- Tooltip/context must continue to identify the visit and recorded measurement.
- Date range controls continue to call `getWeightHistory` with the selected range.

## Non-Goals

- No change to `/display/summary`.
- No change to backup/restore archive format.
- No change to cat identification, visit creation, or visit editing.
- No medical alerting or health interpretation.
