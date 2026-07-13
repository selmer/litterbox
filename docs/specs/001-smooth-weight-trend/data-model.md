# Data Model: Smooth Weight Trend

## Cat

Represents one animal whose weight history appears in the dashboard graph.

**Existing source fields used**

- `cat_id`: Stable identifier from weight history response.
- `cat_name`: Display name and chart series key.

**Relationships**

- Has many weight measurements.
- Has one derived chart series in the dashboard graph.

**Validation rules**

- Smoothing is isolated per `cat_id`/`cat_name`.
- Measurements from different cats must never influence each other's trend.

## Weight Measurement

Represents an original recorded weight point from a visit.

**Existing source fields used**

- `timestamp`: Visit timestamp used for ordering and date-axis placement.
- `weight_kg`: Original recorded weight value.
- `visit_id`: Visit identifier shown in chart context.
- `weight_confidence`: Existing confidence value; ignored weights are excluded by the existing API default.

**Relationships**

- Belongs to one cat.
- Contributes to one derived trend point when usable.

**Validation rules**

- Original `weight_kg` is never modified by the smoothing presentation.
- Non-finite, missing, or otherwise unusable values are not used to derive smoothed trend values.
- Points retain visit identity and timestamp context after smoothing.

## Weight Trend Point

Derived presentation value used by the chart renderer.

**Derived fields**

- `timestamp`: Same timestamp as the source measurement.
- `display_weight_kg`: Weight value used to draw the visible trend line.
- `recorded_weight_kg`: Original source measurement retained for tooltip/context.
- `visit_id`: Source visit identifier.
- `cat_name`: Series key for chart rendering.

**Relationships**

- Derived from one weight measurement and nearby same-cat measurements.
- Belongs to one cat chart series.

**Validation rules**

- For cats with fewer than three usable measurements, `display_weight_kg` equals `recorded_weight_kg`.
- For cats with enough measurements, `display_weight_kg` reduces short-term reversals while preserving sustained direction changes.
- Trend points are sorted chronologically before rendering.
- Large gaps must not create false confidence through invented intermediate measurements.

## State Transitions

No persisted entity state transitions are introduced. The display state is derived at render time:

1. Load weight history from the existing API.
2. Group measurements by cat as returned by the API.
3. Derive same-cat trend points for chart display.
4. Merge trend points into chronological chart rows.
5. Render visible trend while retaining recorded measurement context.
