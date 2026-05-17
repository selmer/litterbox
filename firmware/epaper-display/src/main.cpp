#include <Arduino.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <WiFi.h>

#include <GxEPD2_3C.h>
#include <Fonts/FreeMono9pt7b.h>
#include <Fonts/FreeMonoBold9pt7b.h>
#include <Fonts/FreeMonoBold12pt7b.h>
#include <Fonts/FreeMonoBold18pt7b.h>

#include "config.h"

#ifndef EPD_BUSY_PIN
#define EPD_BUSY_PIN 4
#endif
#ifndef EPD_RST_PIN
#define EPD_RST_PIN 16
#endif
#ifndef EPD_DC_PIN
#define EPD_DC_PIN 17
#endif
#ifndef EPD_CS_PIN
#define EPD_CS_PIN 5
#endif
#ifndef EPD_SCK_PIN
#define EPD_SCK_PIN 18
#endif
#ifndef EPD_MOSI_PIN
#define EPD_MOSI_PIN 23
#endif
#ifndef EPD_RESET_DURATION_MS
#define EPD_RESET_DURATION_MS 2
#endif

namespace {
constexpr uint32_t SerialBaud = 115200;
constexpr uint32_t WifiConnectTimeoutMs = 20000;
constexpr int16_t DisplayWidth = 400;
constexpr int16_t DisplayHeight = 300;

GxEPD2_3C<GxEPD2_420c_Z21, GxEPD2_420c_Z21::HEIGHT> display(
  GxEPD2_420c_Z21(EPD_CS_PIN, EPD_DC_PIN, EPD_RST_PIN, EPD_BUSY_PIN)
);

uint32_t refreshDelayMs(uint32_t refreshSeconds) {
  if (refreshSeconds == 0) {
    refreshSeconds = DEFAULT_REFRESH_SECONDS;
  }
  return refreshSeconds * 1000UL;
}

void connectWifi() {
  if (WiFi.status() == WL_CONNECTED) {
    return;
  }

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.printf("Connecting to WiFi SSID '%s'", WIFI_SSID);
  const uint32_t startedAt = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startedAt < WifiConnectTimeoutMs) {
    Serial.print('.');
    delay(500);
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("WiFi connected, IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("WiFi connection timed out");
  }
}

void printNullableString(JsonVariantConst value) {
  if (value.isNull()) {
    Serial.print("null");
  } else {
    Serial.print(value.as<const char*>());
  }
}

const char* nullableText(JsonVariantConst value, const char* fallback = "-") {
  return value.isNull() ? fallback : value.as<const char*>();
}

void printPayloadPreview(const String& payload) {
  constexpr size_t MaxPreviewChars = 240;
  Serial.print("Payload preview: ");
  for (size_t i = 0; i < payload.length() && i < MaxPreviewChars; ++i) {
    const char c = payload[i];
    Serial.print((c == '\n' || c == '\r') ? ' ' : c);
  }
  if (payload.length() > MaxPreviewChars) {
    Serial.print("...");
  }
  Serial.println();
}

String formatDuration(JsonVariantConst value) {
  if (value.isNull()) {
    return "-";
  }
  const int seconds = value.as<int>();
  const int minutes = seconds / 60;
  const int remainingSeconds = seconds % 60;
  if (minutes == 0) {
    return String(remainingSeconds) + "s";
  }
  return String(minutes) + "m " + String(remainingSeconds) + "s";
}

String formatWeight(JsonVariantConst value) {
  if (value.isNull()) {
    return "-";
  }
  char buffer[16];
  snprintf(buffer, sizeof(buffer), "%.3f kg", value.as<float>());
  return String(buffer);
}

void drawText(int16_t x, int16_t y, const String& text, const GFXfont* font, uint16_t color) {
  display.setFont(font);
  display.setTextColor(color);
  display.setCursor(x, y);
  display.print(text);
}

void drawText(int16_t x, int16_t y, const char* text, const GFXfont* font, uint16_t color) {
  drawText(x, y, String(text), font, color);
}

void drawRightText(int16_t rightX, int16_t y, const String& text, const GFXfont* font, uint16_t color) {
  int16_t x1 = 0;
  int16_t y1 = 0;
  uint16_t w = 0;
  uint16_t h = 0;
  display.setFont(font);
  display.getTextBounds(text, 0, y, &x1, &y1, &w, &h);
  drawText(rightX - static_cast<int16_t>(w), y, text, font, color);
}

String truncateText(const String& value, size_t maxChars) {
  if (value.length() <= maxChars) {
    return value;
  }
  if (maxChars <= 1) {
    return value.substring(0, maxChars);
  }
  return value.substring(0, maxChars - 1) + "~";
}

void drawLabelValue(int16_t x, int16_t y, const char* label, const String& value) {
  drawText(x, y, label, &FreeMono9pt7b, GxEPD_BLACK);
  drawText(x, y + 22, value, &FreeMonoBold9pt7b, GxEPD_BLACK);
}

void drawNoDataChart(int16_t x, int16_t y, int16_t w, int16_t h, const char* message) {
  display.drawRect(x, y, w, h, GxEPD_BLACK);
  drawText(x + 12, y + (h / 2) + 5, message, &FreeMono9pt7b, GxEPD_BLACK);
}

void drawWeightChart(JsonVariantConst chart, int16_t x, int16_t y, int16_t w, int16_t h) {
  display.drawRect(x, y, w, h, GxEPD_BLACK);
  drawText(x + 8, y + 18, "30d weight", &FreeMono9pt7b, GxEPD_BLACK);

  if (chart.isNull()) {
    drawText(x + 8, y + 52, "Not enough data", &FreeMono9pt7b, GxEPD_BLACK);
    return;
  }

  JsonArrayConst points = chart["points"].as<JsonArrayConst>();
  if (points.size() < 2) {
    drawText(x + 8, y + 52, "Not enough data", &FreeMono9pt7b, GxEPD_BLACK);
    return;
  }

  const float minKg = chart["min_kg"].as<float>();
  const float maxKg = chart["max_kg"].as<float>();
  const float range = max(0.001f, maxKg - minKg);
  const int16_t chartX = x + 8;
  const int16_t chartY = y + 30;
  const int16_t chartW = w - 16;
  const int16_t chartH = h - 48;

  char maxLabel[16];
  char minLabel[16];
  snprintf(maxLabel, sizeof(maxLabel), "%.2f", maxKg);
  snprintf(minLabel, sizeof(minLabel), "%.2f", minKg);
  drawText(x + 8, y + h - 22, minLabel, &FreeMono9pt7b, GxEPD_BLACK);
  drawRightText(x + w - 8, y + h - 22, maxLabel, &FreeMono9pt7b, GxEPD_BLACK);

  int16_t previousX = chartX;
  int16_t previousY = chartY + chartH;
  bool hasPrevious = false;
  const size_t lastIndex = points.size() - 1;
  size_t index = 0;
  for (JsonObjectConst point : points) {
    const float weight = point["weight_kg"].as<float>();
    const int16_t px = chartX + static_cast<int16_t>((chartW * index) / lastIndex);
    const int16_t py = chartY + chartH - static_cast<int16_t>(((weight - minKg) / range) * chartH);
    display.fillCircle(px, py, 2, GxEPD_BLACK);
    if (hasPrevious) {
      display.drawLine(previousX, previousY, px, py, GxEPD_BLACK);
    }
    previousX = px;
    previousY = py;
    hasPrevious = true;
    ++index;
  }
}


String formatCompactWeight(JsonVariantConst value) {
  if (value.isNull()) {
    return "--";
  }
  char buffer[16];
  snprintf(buffer, sizeof(buffer), "%.2f kg", value.as<float>());
  return String(buffer);
}

String formatDelta(JsonVariantConst value) {
  if (value.isNull()) {
    return "--";
  }
  const float delta = value.as<float>();
  char buffer[16];
  snprintf(buffer, sizeof(buffer), "%+.2f", delta);
  return String(buffer);
}

uint16_t deltaColor(JsonVariantConst value) {
  if (value.isNull()) {
    return GxEPD_BLACK;
  }
  return value.as<float>() < -0.10f ? GxEPD_RED : GxEPD_BLACK;
}

void drawTinySparkline(JsonArrayConst values, int16_t x, int16_t y, int16_t w, int16_t h) {
  if (values.size() < 2) {
    display.drawLine(x, y + h / 2, x + w, y + h / 2, GxEPD_BLACK);
    return;
  }

  float minValue = values[0].as<float>();
  float maxValue = minValue;
  for (JsonVariantConst value : values) {
    const float weight = value.as<float>();
    minValue = min(minValue, weight);
    maxValue = max(maxValue, weight);
  }
  const float range = max(0.001f, maxValue - minValue);
  const size_t lastIndex = values.size() - 1;

  int16_t previousX = x;
  int16_t previousY = y + h;
  bool hasPrevious = false;
  size_t index = 0;
  for (JsonVariantConst value : values) {
    const float weight = value.as<float>();
    const int16_t px = x + static_cast<int16_t>((w * index) / lastIndex);
    const int16_t py = y + h - static_cast<int16_t>(((weight - minValue) / range) * h);
    if (hasPrevious) {
      display.drawLine(previousX, previousY, px, py, GxEPD_BLACK);
    }
    display.fillCircle(px, py, 1, GxEPD_BLACK);
    previousX = px;
    previousY = py;
    hasPrevious = true;
    ++index;
  }
}

void drawComparison(int16_t x, int16_t y, const char* label, JsonVariantConst comparison) {
  drawText(x, y, label, &FreeMono9pt7b, GxEPD_BLACK);
  if (comparison.isNull()) {
    drawText(x, y + 19, "--", &FreeMonoBold9pt7b, GxEPD_BLACK);
    return;
  }
  drawText(x, y + 19, formatCompactWeight(comparison["weight_kg"]), &FreeMonoBold9pt7b, GxEPD_BLACK);
  drawText(x, y + 38, formatDelta(comparison["delta_kg"]), &FreeMono9pt7b, deltaColor(comparison["delta_kg"]));
}

void drawCatComparisonRow(JsonObjectConst cat, int16_t y, int16_t h) {
  display.drawRect(10, y, DisplayWidth - 20, h, GxEPD_BLACK);

  const String name = truncateText(nullableText(cat["name"], "Cat"), 12);
  drawText(22, y + 29, name, &FreeMonoBold12pt7b, GxEPD_BLACK);
  drawText(22, y + 55, "visits", &FreeMono9pt7b, GxEPD_BLACK);
  drawText(92, y + 58, String(cat["visits_today"].as<int>()), &FreeMonoBold18pt7b, GxEPD_BLACK);

  drawText(140, y + 21, "latest", &FreeMono9pt7b, GxEPD_BLACK);
  drawText(140, y + 50, formatCompactWeight(cat["latest_weight_kg"]), &FreeMonoBold12pt7b, GxEPD_BLACK);

  drawComparison(238, y + 21, "1m", cat["one_month_ago"]);
  drawComparison(315, y + 21, "3m", cat["three_months_ago"]);

  JsonArrayConst sparkline = cat["sparkline"].as<JsonArrayConst>();
  drawTinySparkline(sparkline, 22, y + h - 22, 92, 12);
}

void drawSummary(JsonDocument& doc) {
  const bool healthy = doc["status"]["healthy"].as<bool>();
  const bool alert = !doc["alert"].isNull();
  const uint16_t accent = (!healthy || alert) ? GxEPD_RED : GxEPD_BLACK;

  display.setRotation(0);
  display.setFullWindow();
  display.firstPage();
  do {
    display.fillScreen(GxEPD_WHITE);

    if (!doc["alert"].isNull()) {
      display.fillRect(10, 10, DisplayWidth - 20, 24, GxEPD_RED);
      drawText(16, 28, truncateText(nullableText(doc["alert"]), 38), &FreeMonoBold9pt7b, GxEPD_WHITE);
    }

    JsonArrayConst cats = doc["cats"].as<JsonArrayConst>();
    if (cats.size() == 0) {
      JsonObjectConst today = doc["today"];
      drawText(22, 58, "No cat data", &FreeMonoBold18pt7b, GxEPD_BLACK);
      drawText(24, 106, "Visits today", &FreeMono9pt7b, GxEPD_BLACK);
      drawText(24, 158, String(today["visits"].as<int>()), &FreeMonoBold18pt7b, GxEPD_BLACK);
    } else if (cats.size() == 1) {
      JsonObjectConst cat = cats[0];
      drawText(18, 52, truncateText(nullableText(cat["name"], "Cat"), 16), &FreeMonoBold18pt7b, GxEPD_BLACK);

      drawText(24, 100, "visits today", &FreeMono9pt7b, GxEPD_BLACK);
      drawText(62, 152, String(cat["visits_today"].as<int>()), &FreeMonoBold18pt7b, GxEPD_BLACK);

      drawText(210, 100, "latest weight", &FreeMono9pt7b, GxEPD_BLACK);
      drawText(210, 152, formatCompactWeight(cat["latest_weight_kg"]), &FreeMonoBold18pt7b, GxEPD_BLACK);

      display.drawLine(10, 182, DisplayWidth - 10, 182, GxEPD_BLACK);
      drawComparison(24, 214, "1 month", cat["one_month_ago"]);
      drawComparison(178, 214, "3 months", cat["three_months_ago"]);
      drawTinySparkline(cat["sparkline"].as<JsonArrayConst>(), 304, 214, 70, 28);
    } else {
      drawCatComparisonRow(cats[0].as<JsonObjectConst>(), 18, 116);
      drawCatComparisonRow(cats[1].as<JsonObjectConst>(), 148, 116);
    }

    drawRightText(DisplayWidth - 10, 292, nullableText(doc["generated_at"]), &FreeMono9pt7b, GxEPD_BLACK);
  } while (display.nextPage());
}

void printSummary(JsonDocument& doc) {
  Serial.println("--- display summary ---");
  Serial.print("generated_at: ");
  printNullableString(doc["generated_at"]);
  Serial.println();

  JsonObjectConst status = doc["status"];
  Serial.print("status: ");
  printNullableString(status["label"]);
  Serial.print(status["healthy"].as<bool>() ? " healthy" : " unhealthy");
  Serial.print(" last_successful_at=");
  printNullableString(status["last_successful_at"]);
  Serial.print(" message=");
  printNullableString(status["message"]);
  Serial.println();

  JsonVariantConst latestVisit = doc["latest_visit"];
  if (latestVisit.isNull()) {
    Serial.println("latest_visit: none");
  } else {
    Serial.print("latest_visit: ");
    printNullableString(latestVisit["cat_name"]);
    Serial.print(latestVisit["identified"].as<bool>() ? " identified" : " unidentified");
    Serial.print(" weight_kg=");
    Serial.print(latestVisit["weight_kg"].isNull() ? NAN : latestVisit["weight_kg"].as<float>(), 3);
    Serial.print(" duration_seconds=");
    Serial.print(latestVisit["duration_seconds"].isNull() ? -1 : latestVisit["duration_seconds"].as<int>());
    Serial.print(" time_ago=");
    printNullableString(latestVisit["time_ago_label"]);
    Serial.println();
  }

  JsonObjectConst today = doc["today"];
  Serial.printf(
    "today: visits=%d time_in_box_seconds=%d cleaning_cycles=%d unidentified=%d\n",
    today["visits"].as<int>(),
    today["time_in_box_seconds"].as<int>(),
    today["cleaning_cycles"].as<int>(),
    today["unidentified_visits"].as<int>()
  );

  JsonVariantConst chart = doc["chart"];
  if (chart.isNull()) {
    Serial.println("chart: none");
  } else {
    JsonArrayConst points = chart["points"].as<JsonArrayConst>();
    Serial.printf(
      "chart: %s points=%u min=%.3f max=%.3f\n",
      chart["label"].as<const char*>(),
      static_cast<unsigned>(points.size()),
      chart["min_kg"].as<float>(),
      chart["max_kg"].as<float>()
    );
    for (JsonObjectConst point : points) {
      Serial.printf("  %s %.3f kg\n", point["date"].as<const char*>(), point["weight_kg"].as<float>());
    }
  }

  JsonArrayConst cats = doc["cats"].as<JsonArrayConst>();
  Serial.printf("cats: %u\n", static_cast<unsigned>(cats.size()));
  for (JsonObjectConst cat : cats) {
    Serial.print("  ");
    printNullableString(cat["name"]);
    Serial.print(" visits_today=");
    Serial.print(cat["visits_today"].as<int>());
    Serial.print(" last_weight_kg=");
    if (cat["last_weight_kg"].isNull()) {
      Serial.print("null");
    } else {
      Serial.print(cat["last_weight_kg"].as<float>(), 3);
    }
    Serial.println();
  }

  Serial.print("alert: ");
  printNullableString(doc["alert"]);
  Serial.println();
  Serial.println("-----------------------");
}

uint32_t fetchPrintAndRenderSummary() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Skipping fetch: WiFi is not connected");
    return DEFAULT_REFRESH_SECONDS;
  }

  HTTPClient http;
  http.setTimeout(HTTP_TIMEOUT_MS);
  http.begin(DISPLAY_SUMMARY_URL);
  http.addHeader("Accept", "application/json");
  http.addHeader("Accept-Encoding", "identity");

  Serial.print("GET ");
  Serial.println(DISPLAY_SUMMARY_URL);
  const int statusCode = http.GET();
  if (statusCode != HTTP_CODE_OK) {
    Serial.printf("HTTP error: %d\n", statusCode);
    http.end();
    return DEFAULT_REFRESH_SECONDS;
  }

  const String contentType = http.header("Content-Type");
  const String payload = http.getString();
  http.end();

  if (contentType.length() > 0 && contentType.indexOf("application/json") < 0) {
    Serial.print("Unexpected Content-Type: ");
    Serial.println(contentType);
    Serial.print("Payload length: ");
    Serial.println(payload.length());
    printPayloadPreview(payload);
    return DEFAULT_REFRESH_SECONDS;
  }

  JsonDocument doc;
  DeserializationError error = deserializeJson(doc, payload);
  if (error) {
    Serial.print("JSON parse error: ");
    Serial.println(error.c_str());
    Serial.print("Payload length: ");
    Serial.println(payload.length());
    printPayloadPreview(payload);
    return DEFAULT_REFRESH_SECONDS;
  }

  printSummary(doc);
  drawSummary(doc);
  return doc["refresh_after_seconds"] | DEFAULT_REFRESH_SECONDS;
}
}  // namespace

void setup() {
  Serial.begin(SerialBaud);
  delay(1000);
  Serial.println();
  Serial.println("Litterbox e-paper display booting");

  SPI.begin(EPD_SCK_PIN, -1, EPD_MOSI_PIN, EPD_CS_PIN);
  display.init(SerialBaud, true, EPD_RESET_DURATION_MS, false);
  display.setRotation(0);
  display.fillScreen(GxEPD_WHITE);
  display.hibernate();

  connectWifi();
}

void loop() {
  connectWifi();
  const uint32_t refreshSeconds = fetchPrintAndRenderSummary();
  display.hibernate();
  Serial.printf("Waiting %u seconds before next refresh\n", refreshSeconds);
  delay(refreshDelayMs(refreshSeconds));
}
