/*
  Smart Home Controller
  Tier: Option B (Recommended) - Arduino UNO / ESP32
  Hardware: PIR motion sensor, LDR (voltage divider), DHT11 temperature sensor,
            relay/LED for light, relay/LED for fan, buzzer, red+green LED,
            16x2 LCD, manual switches

  Logic mirrors simulation/smart_home_state.py exactly:
  Priority order -> SECURITY > MANUAL OVERRIDE > AUTOMATIC
*/

#include <LiquidCrystal.h>
#include <DHT.h>

// ---------- Configuration ----------
const int DARK_THRESHOLD = 400;      // LDR analog reading, lower = darker (0-1023)
const float TEMP_ON_THRESHOLD = 28.0;
const float TEMP_OFF_THRESHOLD = 26.0;
const unsigned long MOTION_LIGHT_TIMEOUT = 6000; // ms

// ---------- Pins ----------
const int PIR_PIN = 2;
const int LDR_PIN = A0;
const int DHT_PIN = 3;
const int LIGHT_RELAY_PIN = 4;
const int FAN_RELAY_PIN = 5;
const int BUZZER_PIN = 6;
const int RED_LED_PIN = 7;
const int GREEN_LED_PIN = 8;
const int SECURITY_SWITCH_PIN = 9;
const int MANUAL_SWITCH_PIN = 10;
const int MANUAL_LIGHT_BTN = 11;
const int MANUAL_FAN_BTN = 12;

const int LCD_RS = A1, LCD_EN = A2, LCD_D4 = A3, LCD_D5 = A4, LCD_D6 = A5, LCD_D7 = 13;

DHT dht(DHT_PIN, DHT11);
LiquidCrystal lcd(LCD_RS, LCD_EN, LCD_D4, LCD_D5, LCD_D6, LCD_D7);

// ---------- State ----------
bool motionDetected = false;
unsigned long lastMotionAt = 0;
bool lightOn = false;
bool fanOn = false;
bool securityMode = false;
bool manualOverride = false;

void setup() {
  Serial.begin(9600);
  dht.begin();
  lcd.begin(16, 2);

  pinMode(PIR_PIN, INPUT);
  pinMode(LIGHT_RELAY_PIN, OUTPUT);
  pinMode(FAN_RELAY_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(RED_LED_PIN, OUTPUT);
  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(SECURITY_SWITCH_PIN, INPUT_PULLUP);
  pinMode(MANUAL_SWITCH_PIN, INPUT_PULLUP);
  pinMode(MANUAL_LIGHT_BTN, INPUT_PULLUP);
  pinMode(MANUAL_FAN_BTN, INPUT_PULLUP);

  digitalWrite(GREEN_LED_PIN, HIGH); // system nominal
  lcd.print("Smart Home Rdy");
}

void loop() {
  // ---- Read inputs ----
  int pirState = digitalRead(PIR_PIN);
  if (pirState == HIGH) {
    motionDetected = true;
    lastMotionAt = millis();
  } else if (millis() - lastMotionAt > MOTION_LIGHT_TIMEOUT) {
    motionDetected = false;
  }

  int ldrValue = analogRead(LDR_PIN);
  bool isDark = ldrValue < DARK_THRESHOLD;

  float temperature = dht.readTemperature();
  if (isnan(temperature)) temperature = 25.0; // fallback on sensor error

  securityMode = digitalRead(SECURITY_SWITCH_PIN) == LOW;
  manualOverride = digitalRead(MANUAL_SWITCH_PIN) == LOW;

  // ---- PRIORITY 1: SECURITY ----
  bool alert = securityMode && motionDetected;
  digitalWrite(BUZZER_PIN, alert ? HIGH : LOW);
  digitalWrite(RED_LED_PIN, alert ? HIGH : LOW);

  // ---- PRIORITY 2: MANUAL OVERRIDE ----
  if (manualOverride) {
    lightOn = digitalRead(MANUAL_LIGHT_BTN) == LOW;
    fanOn = digitalRead(MANUAL_FAN_BTN) == LOW;
  } else {
    // ---- PRIORITY 3: AUTOMATIC ----
    if (motionDetected && isDark) lightOn = true;
    else if (!motionDetected) lightOn = false;

    if (temperature > TEMP_ON_THRESHOLD) fanOn = true;
    else if (temperature < TEMP_OFF_THRESHOLD) fanOn = false;
  }

  digitalWrite(LIGHT_RELAY_PIN, lightOn ? HIGH : LOW);
  digitalWrite(FAN_RELAY_PIN, fanOn ? HIGH : LOW);

  // ---- Display ----
  lcd.clear();
  lcd.setCursor(0, 0);
  if (alert) {
    lcd.print("INTRUDER ALERT!");
  } else {
    lcd.print("T:");
    lcd.print(temperature, 1);
    lcd.print("C L:");
    lcd.print(isDark ? "DRK" : "BRT");
  }
  lcd.setCursor(0, 1);
  lcd.print(lightOn ? "Light:ON " : "Light:OFF ");
  lcd.print(fanOn ? "Fan:ON" : "Fan:OFF");

  // ---- Serial monitor (matches simulation event format) ----
  Serial.print("Temperature: "); Serial.print(temperature); Serial.println(" C");
  Serial.print("Room: "); Serial.println(isDark ? "DARK" : "BRIGHT");
  Serial.print("Motion: "); Serial.println(motionDetected ? "DETECTED" : "NONE");
  Serial.print("Light: "); Serial.println(lightOn ? "ON" : "OFF");
  Serial.print("Fan: "); Serial.println(fanOn ? "ON" : "OFF");
  Serial.print("Security: "); Serial.println(alert ? "ALERT" : "SAFE");
  Serial.println("---");

  delay(1000);
}
