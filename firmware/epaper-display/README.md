# Litterbox ESP32 E-Paper Display

PlatformIO firmware scaffold for an ESP32 view on the Litterbox app.

Current milestone: connect to WiFi, fetch `GET /display/summary`, parse the JSON payload, print the display contract to Serial, and render a first 400x300 black/white/red e-paper dashboard.

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

## Default ESP32 DevKit v1 wiring

The scaffold assumes this wiring unless you override it in `include/config.h`:

| E-paper pin | ESP32 DevKit v1 GPIO |
|---|---:|
| BUSY | 4 |
| RST | 16 |
| DC | 17 |
| CS | 5 |
| CLK/SCK | 18 |
| DIN/MOSI | 23 |
| GND | GND |
| VCC | 3V3 |

If your wiring differs, change `EPD_BUSY_PIN`, `EPD_RST_PIN`, `EPD_DC_PIN`, `EPD_CS_PIN`, `EPD_SCK_PIN`, and `EPD_MOSI_PIN` in `include/config.h`.

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

Tune the physical e-paper layout on real hardware:

- confirm pin mapping and driver class
- verify red/black/white rendering
- adjust rotation if the screen is upside down or portrait
- tune text sizes and chart placement for readability

Keep the chart rendering isolated so it can be removed if it is too busy on e-paper.
