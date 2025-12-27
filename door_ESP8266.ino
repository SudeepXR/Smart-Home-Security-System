#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>
#include <ESPAsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <ArduinoJson.h>
#include <time.h>

// ----------------------
// WiFi
// ----------------------
const char* ssid = "name";
const char* password = "password";

// ----------------------
// Telegram
// ----------------------
const char* botToken = "insert";
String chatID = "insert";

String pendingMessage = "";
bool pendingSend = false;

// ----------------------
// System State
// ----------------------
bool isArmed = false;
String currentMode = "normal";


// ----------------------
// Time (IST)
// ----------------------
const long gmtOffset_sec = 19800;
const int daylightOffset_sec = 0;

// ----------------------
// Pins
// ----------------------
const int FIXED_LED = D4;              // Fixed-time LED
const int BUTTON_PIN = D2;             // Child mode button

const int night_LEDS[] = {D1, D5, D6, D7};
const int NUM_night_LEDS = 4;
bool lastNightState[NUM_night_LEDS] = {false};

// ----------------------
// Server
// ----------------------
AsyncWebServer server(80);

// ----------------------
// Child mode vars
// ----------------------
unsigned long lastDebounceTime = 0;
unsigned long lastReminderTime = 0;
bool doorWasOpenPrinted = false;
int lastRaw = HIGH;
int stable = HIGH;

// ----------------------
// Night simulation vars
// ----------------------
unsigned long nextnightChange = 0;

// ----------------------
// Telegram helpers
// ----------------------
void notify(String msg) {
  Serial.println(msg);
  if (!isArmed) return;
  pendingMessage = msg;
  pendingSend = true;
}

void notifyAlways(String msg) {
  Serial.println(msg);
  pendingMessage = msg;
  pendingSend = true;
}


void sendTelegramNow(String msg) {
  WiFiClientSecure client;
  client.setInsecure();
  if (!client.connect("api.telegram.org", 443)) return;

  String url = "/bot" + String(botToken) +
               "/sendMessage?chat_id=" + chatID +
               "&text=" + msg;

  client.print(String("GET ") + url + " HTTP/1.1\r\n"
               "Host: api.telegram.org\r\n"
               "Connection: close\r\n\r\n");
}

// ----------------------
// MODE HANDLER (FIXED)
// ----------------------
void parseBodyAndHandleMode(const String &body, AsyncWebServerRequest *request) {
  StaticJsonDocument<200> doc;
  if (deserializeJson(doc, body)) {
    request->send(400, "application/json", "{\"error\":\"invalid_json\"}");
    return;
  }

  if (!isArmed) {
    Serial.println("⚠️ Mode ignored (UNARMED)");
    request->send(200, "application/json", "{\"status\":\"ignored_unarmed\"}");
    return;
  }

  String requestedMode = doc["mode"].as<String>();

  if (requestedMode == "night") {
    currentMode = "night";
    notify("🏠 Presence Simulator ACTIVATED");
    Serial.println("🌙 Night mapped to Presence Simulator");
  } else {
    currentMode = requestedMode;
    notify("Mode changed to: " + currentMode);
  }

  request->send(200, "application/json", "{\"status\":\"ok\"}");
}

// ----------------------
// ARM HANDLER
// ----------------------
void parseBodyAndHandleArm(const String &body, AsyncWebServerRequest *request) {
  StaticJsonDocument<200> doc;
  if (deserializeJson(doc, body)) {
    request->send(400, "application/json", "{\"error\":\"invalid_json\"}");
    return;
  }

  isArmed = doc["armed"].as<bool>();

  if (isArmed) {
    notify("🔐 System ARMED");
  } else {
    notifyAlways("🔓 System DISARMED");
    digitalWrite(FIXED_LED, LOW);
    for (int i = 0; i < NUM_night_LEDS; i++)
      digitalWrite(night_LEDS[i], LOW);
  }

  request->send(200, "application/json", "{\"status\":\"ok\"}");
}


// ----------------------
// SETUP
// ----------------------
void setup() {
  Serial.begin(115200);
  delay(300);

  pinMode(FIXED_LED, OUTPUT);
  digitalWrite(FIXED_LED, LOW);

  for (int i = 0; i < NUM_night_LEDS; i++) {
    pinMode(night_LEDS[i], OUTPUT);
    digitalWrite(night_LEDS[i], LOW);
  }

  pinMode(BUTTON_PIN, INPUT_PULLUP);

  Serial.println("\nConnecting to WiFi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(200);
    Serial.print(".");
  }

  Serial.println("\nConnected! IP:");
  Serial.println(WiFi.localIP());

  configTime(gmtOffset_sec, daylightOffset_sec, "pool.ntp.org");

  DefaultHeaders::Instance().addHeader("Access-Control-Allow-Origin", "*");
  DefaultHeaders::Instance().addHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  DefaultHeaders::Instance().addHeader("Access-Control-Allow-Headers", "*");

  server.onRequestBody([](AsyncWebServerRequest *req, uint8_t *data, size_t len, size_t, size_t) {
    String body;
    for (size_t i = 0; i < len; i++) body += (char)data[i];

    if (req->url() == "/mode") parseBodyAndHandleMode(body, req);
    else if (req->url() == "/arm") parseBodyAndHandleArm(body, req);
    else req->send(404);
  });

  server.begin();
  Serial.println("🚀 Server running");
}

// ----------------------
// LOOP
// ----------------------
void loop() {

if (pendingSend) {
  sendTelegramNow(pendingMessage);
  pendingSend = false;
}


  if (!isArmed) return;

  // ----------------------
  // GLOBAL FIXED LED (D4)
  // ----------------------

  time_t now = time(nullptr);
  struct tm *t = localtime(&now);

  bool fixedOn =
    (t->tm_hour > 18 || (t->tm_hour == 18 && t->tm_min >= 30)) ||
    (t->tm_hour < 5);

  digitalWrite(FIXED_LED, fixedOn ? HIGH : LOW);

 // ----------------------
// NIGHT / PRESENCE MODE (ALWAYS CHANGING)
// ----------------------
if (currentMode == "night") {

  if (millis() > nextnightChange) {

    bool newState[NUM_night_LEDS];
    bool different = false;

    // Keep generating until pattern changes
    do {
      // Reset
      for (int i = 0; i < NUM_night_LEDS; i++)
        newState[i] = false;

      // At least ONE LED
      int howMany = random(1, NUM_night_LEDS + 1);
      bool used[NUM_night_LEDS] = {false};

      for (int i = 0; i < howMany; i++) {
        int idx;
        do {
          idx = random(0, NUM_night_LEDS);
        } while (used[idx]);

        used[idx] = true;
        newState[idx] = true;
      }

      // Check if pattern changed
      different = false;
      for (int i = 0; i < NUM_night_LEDS; i++) {
        if (newState[i] != lastNightState[i]) {
          different = true;
          break;
        }
      }

    } while (!different);

    // Apply new pattern
    for (int i = 0; i < NUM_night_LEDS; i++) {
      digitalWrite(night_LEDS[i], newState[i] ? HIGH : LOW);
      lastNightState[i] = newState[i];
    }

    // 🔥 Demo timing: 1–5 seconds
    nextnightChange = millis() + random(1000UL, 5000UL);
  }

} else {
  // Reset when leaving night mode
  for (int i = 0; i < NUM_night_LEDS; i++) {
    digitalWrite(night_LEDS[i], LOW);
    lastNightState[i] = false;
  }
}


  // ----------------------
  // CHILD MODE (UNCHANGED)
  // ----------------------
  if (currentMode == "child") {

    int reading = digitalRead(BUTTON_PIN);

    if (reading != lastRaw) {
      lastDebounceTime = millis();
      lastRaw = reading;
    }

    if (millis() - lastDebounceTime > 30) {
      if (stable != reading) {
        stable = reading;

        if (stable == LOW) {
          notify("🚨 The door has been OPENED now");
          doorWasOpenPrinted = true;
          lastReminderTime = millis();
        } else if (stable == HIGH && doorWasOpenPrinted) {
          notify("✅ The door has now been CLOSED");
          doorWasOpenPrinted = false;
        }
      }
    }

    if (stable == LOW && doorWasOpenPrinted &&
        millis() - lastReminderTime >= 300000UL) {
      notify("⚠️ DOOR STILL OPEN (after 5-mins)");
      lastReminderTime = millis();
    }
  }
}
