#pragma once

// Copy this file to include/config.h and fill in your local values.
// The real config.h is ignored by git.

#define WIFI_SSID "your-wifi-name"
#define WIFI_PASSWORD "your-wifi-password"

// Use the NAS/server address that serves the FastAPI app on your LAN.
// Example: "http://192.168.68.115:8001/display/summary"
#define DISPLAY_SUMMARY_URL "http://192.168.68.115:8001/display/summary"

// Fallback refresh interval when the backend does not provide one.
#define DEFAULT_REFRESH_SECONDS 3600

// HTTP timeout in milliseconds. Keep this short enough that the display recovers
// from network issues without feeling stuck.
#define HTTP_TIMEOUT_MS 8000

// Default ESP32 DevKit v1 / VSPI wiring for Waveshare 4.2inch e-Paper Module (B).
// Adjust these if your wiring differs.
#define EPD_BUSY_PIN 4
#define EPD_RST_PIN 16
#define EPD_DC_PIN 17
#define EPD_CS_PIN 5
#define EPD_SCK_PIN 18
#define EPD_MOSI_PIN 23

// Waveshare boards often behave better with a short reset pulse.
#define EPD_RESET_DURATION_MS 2
