#pragma once

// Copy this file to include/config.h and fill in your local values.
// The real config.h is ignored by git.

#define WIFI_SSID "your-wifi-name"
#define WIFI_PASSWORD "your-wifi-password"

// Use the NAS/server address that serves the FastAPI app on your LAN.
// Example: "http://192.168.68.115:8001/display/summary"
#define DISPLAY_SUMMARY_URL "http://192.168.68.115:8001/display/summary"

// Fallback refresh interval when the backend does not provide one.
#define DEFAULT_REFRESH_SECONDS 300

// HTTP timeout in milliseconds. Keep this short enough that the display recovers
// from network issues without feeling stuck.
#define HTTP_TIMEOUT_MS 8000
