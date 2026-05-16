# Litterbox ESP32 E-Paper Display

PlatformIO firmware scaffold for an ESP32 view on the Litterbox app.

Current milestone: connect to WiFi, fetch `GET /display/summary`, parse the JSON payload, and print the display contract to Serial. E-paper rendering comes next once the data path is proven on hardware.

## Setup

1. Install PlatformIO.
2. Copy `include/config.example.h` to `include/config.h`.
3. Fill in WiFi credentials and `DISPLAY_SUMMARY_URL`.
4. Build and upload:

```bash
pio run
pio run --target upload
pio device monitor
```

Default board is `esp32dev`. If your ESP32 controller uses a more specific PlatformIO board ID, change `board = esp32dev` in `platformio.ini` before building.

## Expected Serial Output

The first milestone should show:

- WiFi connection and local IP
- HTTP 200 fetch from `/display/summary`
- Poller status
- Latest visit summary
- Today totals
- Optional 30-day chart points
- Per-cat compact rows
- Alert text or `null`

## Next Milestone

Add the Waveshare/Pico 4.2 black/white/red e-paper driver and render a fixed 400x300 landscape layout:

- top status bar
- latest visit block
- compact 30-day sparkline
- today totals strip
- small per-cat rows

Keep the chart rendering isolated so it can be removed if it is too busy on e-paper.
