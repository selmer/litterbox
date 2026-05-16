#include <Arduino.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <WiFi.h>

#include "config.h"

namespace {
constexpr uint32_t SerialBaud = 115200;
constexpr uint32_t WifiConnectTimeoutMs = 20000;

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

uint32_t fetchAndPrintSummary() {
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
  return doc["refresh_after_seconds"] | DEFAULT_REFRESH_SECONDS;
}
}  // namespace

void setup() {
  Serial.begin(SerialBaud);
  delay(1000);
  Serial.println();
  Serial.println("Litterbox e-paper display booting");
  connectWifi();
}

void loop() {
  connectWifi();
  const uint32_t refreshSeconds = fetchAndPrintSummary();
  Serial.printf("Waiting %u seconds before next refresh\n", refreshSeconds);
  delay(refreshDelayMs(refreshSeconds));
}
