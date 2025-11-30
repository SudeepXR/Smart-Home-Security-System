#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>
#include <ESPAsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <ArduinoJson.h>

// ----------------------
// WiFi
// ----------------------
const char* ssid = "sudeep";
const char* password = "Masaladosa";

// ----------------------
// Telegram
// ----------------------
const char* botToken = "8360881658:AAFtXcoROgUZ6xA178aMkz4uaPVN9DgYPy0";
String chatID = "6637316723";

// Telegram queue
String pendingMessage = "";
bool pendingSend = false;

// NEW --> System armed or not
bool isArmed = false;   // 🔥 Default: NOT ARMED

// Safe wrapper to queue sending
void notify(String msg) {

  Serial.println(msg);      

  // 🚨 Don't send Telegram when NOT armed  
  if (!isArmed) return;

  pendingMessage = msg;     
  pendingSend = true;
}

// Actual Telegram sender (HTTPS)
void sendTelegramNow(String msg) {
  WiFiClientSecure client;
  client.setInsecure();  

  if (!client.connect("api.telegram.org", 443)) {
    Serial.println("❌ Telegram connect failed");
    return;
  }

  String url = "/bot" + String(botToken) + "/sendMessage?chat_id=" + chatID + "&text=" + msg;

  client.print(String("GET ") + url + " HTTP/1.1\r\n" +
               "Host: api.telegram.org\r\n" +
               "Connection: close\r\n\r\n");

  Serial.println("📨 Telegram sent: " + msg);
}

// ----------------------
// Pins
// ----------------------
const int LED_PIN = D4;
const int BUTTON_PIN = D2;

AsyncWebServer server(80);
String currentMode = "normal";

// Button tracking
unsigned long lastDebounceTime = 0;
unsigned long lastReminderTime = 0;

bool doorWasOpenPrinted = false;
int lastRaw = HIGH;
int stable = HIGH;

// ----------------------
// MODE HANDLER
// ----------------------
void parseBodyAndHandleMode(const String &body, AsyncWebServerRequest *request) {

  StaticJsonDocument<200> doc;
  if (deserializeJson(doc, body)) {
    request->send(400, "application/json", "{\"error\":\"invalid_json\"}");
    return;
  }

  // If system is UNARMED -> ignore mode change
  if (!isArmed) {
    Serial.println("⚠️ Mode change ignored (system UNARMED)");
    request->send(200, "application/json", "{\"status\":\"ignored_unarmed\"}");
    
    return;
    
  }
  request->send(200, "application/json", "{\"status\":\"activated\"}");

  currentMode = doc["mode"].as<String>();
  notify("Mode changed to: " + currentMode);

  if (currentMode == "night") {
    digitalWrite(LED_PIN, HIGH);
    notify("Mode changed to: night -💡 Light is now ON");
  } else {
    digitalWrite(LED_PIN, LOW);
  }

  request->send(200, "application/json", "{\"status\":\"ok\"}");
}

// ----------------------
// NEW: ARM HANDLER
// ----------------------
void parseBodyAndHandleArm(const String &body, AsyncWebServerRequest *request) {

  StaticJsonDocument<200> doc;
  if (deserializeJson(doc, body)) {
    request->send(400, "application/json", "{\"error\":\"invalid_json\"}");
    return;
  }
  request->send(200, "application/json", "{\"status\":\"ok\"}");
  bool armed = doc["armed"].as<bool>();
  isArmed = armed;

  if (isArmed) {
    notify("🔐 System ARMED");
  } else {
    Serial.println("🔓 System DISARMED — ignoring mode & sensors");
    notify("🔓 System DISARMED");
    digitalWrite(LED_PIN, LOW);  // turn off LED when disarmed
  }

  request->send(200, "application/json", "{\"status\":\"ok\"}");
}

// ----------------------
// SETUP
// ----------------------
void setup() {
  Serial.begin(115200);
  delay(300);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  pinMode(BUTTON_PIN, INPUT_PULLUP);

  Serial.println("\nConnecting to WiFi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(200);
    Serial.print(".");
  }

  Serial.println("\nConnected! IP:");
  Serial.println(WiFi.localIP());

  // CORS
  DefaultHeaders::Instance().addHeader("Access-Control-Allow-Origin", "*");
  DefaultHeaders::Instance().addHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  DefaultHeaders::Instance().addHeader("Access-Control-Allow-Headers", "*");

  server.onNotFound([](AsyncWebServerRequest *request) {
    if (request->method() == HTTP_OPTIONS)
      request->send(200, "text/plain", "OK");
    else request->send(404, "text/plain", "Not found");
  });

  // POST BODY HANDLER
  server.onRequestBody([](AsyncWebServerRequest *req, uint8_t *data, size_t len, size_t, size_t) {
    String body;
    for (size_t i = 0; i < len; i++) body += (char)data[i];

    if (req->url() == "/mode") parseBodyAndHandleMode(body, req);
    else if (req->url() == "/arm") parseBodyAndHandleArm(body, req);      // 🔥 NEW
    else req->send(404, "text/plain", "Not found");
  });

  server.on("/mode", HTTP_GET, [](AsyncWebServerRequest *req) {
    req->send(200, "text/plain", "MODE OK");
  });

  server.on("/arm", HTTP_GET, [](AsyncWebServerRequest *req) {           // 🔥 NEW
    req->send(200, "text/plain", "ARM OK");
  });

  server.begin();
  Serial.println("🚀 Server running");
}

// ----------------------
// LOOP — CHILD MODE
// ----------------------
void loop() {

  // SEND TELEGRAM IF PENDING
  if (pendingSend && isArmed) {     // <-- only send if ARMED
    sendTelegramNow(pendingMessage);
    pendingSend = false;
  }

  // If UNARMED → ignore everything
  if (!isArmed) {
    yield();
    return;
  }

  // Only active in CHILD MODE
  if (currentMode == "child") {

    int reading = digitalRead(BUTTON_PIN);

    // debounce
    if (reading != lastRaw) {
      lastDebounceTime = millis();
      lastRaw = reading;
    }

    if (millis() - lastDebounceTime > 30) {
      if (stable != reading) {
        stable = reading;

        // stable 0 → DOOR OPEN
        if (stable == LOW) {
          notify("🚨 The door has been OPENED now");
          doorWasOpenPrinted = true;
          lastReminderTime = millis();
        }

        // stable 1 → DOOR CLOSED
        else if (stable == HIGH) {
          if (doorWasOpenPrinted) {
            notify("✅ The door has now been CLOSED");
            doorWasOpenPrinted = false;
          }
        }
      }
    }

    // 5-minute reminder
    if (stable == LOW && doorWasOpenPrinted) {
      if (millis() - lastReminderTime >= 300000UL) {
        notify("⚠️ DOOR STILL OPEN (after 5-mins)");
        lastReminderTime = millis();
      }
    }
  }

  yield();
}
