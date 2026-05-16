# ESP32 E-Paper Display View

Priority: P1

Implementation scope:
Specification only. This does not add firmware, backend routes, or frontend code yet. It defines the future API and display behavior for an ESP32-driven 4.2 inch e-paper status view.

## Summary

- Create a future ESP32 display view for the Litterbox app.
- Target hardware is a USB-powered ESP32 controller with a Waveshare/Pico e-paper 4.2 black/white/red display.
- The display acts as a periodically refreshed status view for the app.
- V1 includes a small experimental 30-day weight chart. If it is too busy or slow on e-paper, it should be easy to remove without affecting the rest of the display view.
- Firmware repository placement remains deferred; the likely future default is a same-repo `firmware/epaper-display/` PlatformIO project.

## Key Changes

- Plan a new backend endpoint: `GET /display/summary`.
- Endpoint is LAN-only without authentication in v1, matching the current local app setup.
- Endpoint returns compact JSON for firmware rather than the full web dashboard payload.
- JSON includes status, latest visit, today's totals, compact per-cat rows, an optional alert, and a 30-day chart series.
- ESP32 periodically pulls the endpoint, renders the screen, waits, and refreshes again.
- Default refresh interval is 300 seconds, aligned with the current poller cadence.
- Display target is 400x300 landscape, black/white/red. Red is reserved for warnings, offline/stale states, and unidentified visits.

## API Contract

`GET /display/summary` response:

```json
{
  "generated_at": "2026-05-16T14:30:00Z",
  "refresh_after_seconds": 300,
  "status": {
    "label": "Polling",
    "healthy": true,
    "last_successful_at": "2026-05-16T14:28:00Z",
    "message": null
  },
  "latest_visit": {
    "cat_name": "Plurk",
    "identified": true,
    "started_at": "2026-05-16T12:33:00Z",
    "time_ago_label": "about 2 hours ago",
    "duration_seconds": 300,
    "weight_kg": 3.76,
    "identified_by": "auto"
  },
  "today": {
    "visits": 1,
    "time_in_box_seconds": 300,
    "cleaning_cycles": 0,
    "unidentified_visits": 0
  },
  "chart": {
    "label": "30d weight",
    "unit": "kg",
    "min_kg": 3.62,
    "max_kg": 3.91,
    "points": [
      { "date": "2026-04-16", "weight_kg": 3.72 },
      { "date": "2026-04-23", "weight_kg": 3.78 },
      { "date": "2026-05-01", "weight_kg": 3.69 },
      { "date": "2026-05-16", "weight_kg": 3.76 }
    ]
  },
  "cats": [
    {
      "name": "Plurk",
      "visits_today": 1,
      "last_weight_kg": 3.76
    }
  ],
  "alert": null
}
```

## Fallback Behavior

- No visits yet: `latest_visit` is `null`; the screen shows `No visits yet`; `chart` may be `null`.
- Not enough chart data: chart area shows `Not enough weight data`.
- Unidentified latest visit: `cat_name` is `Unknown cat`, `identified` is `false`, and the display uses a red accent.
- Poller unhealthy: `status.healthy` is `false`, the header/status band uses red, and `status.message` contains the backend error or stale-data message.
- Multiple cats: latest visit remains primary. The chart uses the latest visit's cat when identified, otherwise the first active cat with 30-day data.

## Display Layout

- Top bar: app name, status label, and last update time.
- Main block: latest visit, with cat name as the largest text.
- Main metrics: weight, duration, and time since visit.
- Middle/right compact chart: 30-day weight sparkline, black line on white background.
- Today strip: visits today, time in box, cleaning cycles, and unidentified count.
- Bottom area: compact per-cat rows if space allows.
- Red usage:
  - poller offline or stale
  - unidentified visit
  - alert text
- Chart should be visually secondary: no axes if space is tight, only min/max labels or current weight label.

## Future Firmware Direction

- Use PlatformIO with the Arduino framework as the default future toolchain.
- ESP32 should parse the compact JSON contract rather than the full web dashboard response.
- Firmware should honor `refresh_after_seconds` and avoid refreshing faster than the backend recommends.
- Because the device is expected to be USB-powered, deep sleep and battery optimization are optional rather than required in v1.
- The 30-day chart drawing code should be isolated so the chart can be stripped out cleanly if e-paper readability or refresh speed is poor.

## Acceptance Criteria

- A future implementation can expose `GET /display/summary` without changing the existing web dashboard contract.
- The endpoint can represent normal, no-visit, unidentified, insufficient-chart-data, and unhealthy-poller states.
- The API contract contains enough information for an ESP32 to render the complete 400x300 status screen without additional API calls.
- Chart points are sorted by date and limited to the last 30 days.
- Red is only required for warning, offline/stale, unidentified, or alert states.

## Verification Plan

Backend tests for future implementation:

- `GET /display/summary` returns 200 with the expected schema.
- Handles no visits.
- Handles identified and unidentified latest visits.
- Handles unhealthy poller state.
- Returns 30-day chart points sorted by date.
- Returns `chart: null` or empty points safely when insufficient data exists.
- Aggregates today counts consistently with `/dashboard`.

Firmware acceptance tests for later implementation:

- Compiles with PlatformIO Arduino for ESP32.
- Parses the sample JSON contract.
- Renders all v1 states: normal, no visits, insufficient chart data, unidentified, and poller unhealthy.
- Draws the 30-day chart within its fixed rectangle without overlapping text.
- Does not refresh more often than `refresh_after_seconds`.

Manual verification for later implementation:

- Compare e-paper mock/render against a 400x300 layout.
- Confirm chart remains readable on black/white/red e-paper.
- Confirm red is only used for alert states.

## Assumptions

- Hardware is the 4.2 inch 400x300 black/white/red e-paper variant, based on the Waveshare Pico-ePaper-4.2-B reference: https://www.waveshare.com/wiki/Pico-ePaper-4.2-B
- Device is USB-powered, so deep-sleep battery optimization is optional.
- Firmware repo placement is intentionally deferred; recommendation remains same repo under a future `firmware/epaper-display/` folder.
- The 30-day chart is experimental and should be isolated in the API and layout so it can be removed without affecting the rest of the display view.
