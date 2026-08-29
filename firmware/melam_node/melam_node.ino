// Melam Asan — wrist/stick node firmware
// Board: Seeed XIAO ESP32-S3 (or any ESP32). Sensors: MPU6050 (I2C 0x68), MAX30102 (I2C 0x57).
// Actuator: coin vibration motor via NPN transistor on VIB_PIN. Status LED on LED_PIN.
// Transport: WiFi UDP JSON lines to the hub. Hub replies with haptic commands on the same socket.

#include <WiFi.h>
#include <WiFiUdp.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include "MAX30105.h"
#include "heartRate.h"
#include "config.h"

Adafruit_MPU6050 mpu;
MAX30105 ppg;
WiFiUDP udp;

constexpr int VIB_PIN = 3;
constexpr int LED_PIN = 4;
constexpr uint32_t SAMPLE_HZ = 100;
constexpr uint32_t SAMPLE_US = 1000000 / SAMPLE_HZ;

uint32_t lastSample = 0;
uint32_t lastBeat = 0;
float bpm = 0;
uint32_t vibOffAt = 0;

void setupSensors() {
  Wire.begin();
  if (!mpu.begin()) { Serial.println("MPU6050 not found"); }
  mpu.setAccelerometerRange(MPU6050_RANGE_16_G);   // drum strikes saturate 8G easily
  mpu.setGyroRange(MPU6050_RANGE_2000_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_184_HZ);
  if (ppg.begin(Wire, I2C_SPEED_FAST)) {
    ppg.setup(0x1F, 4, 2, 400, 411, 4096);
  } else {
    Serial.println("MAX30102 not found (fatigue features disabled)");
  }
}

void setupWifi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) { delay(200); Serial.print("."); }
  udp.begin(NODE_PORT);
  Serial.printf("\nnode %s up at %s\n", NODE_ID, WiFi.localIP().toString().c_str());
}

void setup() {
  Serial.begin(115200);
  pinMode(VIB_PIN, OUTPUT); pinMode(LED_PIN, OUTPUT);
  setupSensors();
  setupWifi();
  pulse(120);  // boot confirmation
}

void pulse(uint16_t ms) {
  digitalWrite(VIB_PIN, HIGH); digitalWrite(LED_PIN, HIGH);
  vibOffAt = millis() + ms;
}

void updateHeartRate() {
  long ir = ppg.getIR();
  if (checkForBeat(ir)) {
    uint32_t now = millis();
    float delta = (now - lastBeat) / 1000.0f;
    lastBeat = now;
    float inst = 60.0f / delta;
    if (inst > 30 && inst < 220) bpm = bpm == 0 ? inst : 0.8f * bpm + 0.2f * inst;
  }
}

void sendSample() {
  sensors_event_t a, g, t;
  mpu.getEvent(&a, &g, &t);
  char buf[192];
  snprintf(buf, sizeof(buf),
    "{\"id\":\"%s\",\"t\":%lu,\"ax\":%.2f,\"ay\":%.2f,\"az\":%.2f,\"gx\":%.1f,\"gy\":%.1f,\"gz\":%.1f,\"bpm\":%.0f}",
    NODE_ID, (unsigned long)micros(), a.acceleration.x, a.acceleration.y, a.acceleration.z,
    g.gyro.x, g.gyro.y, g.gyro.z, bpm);
  udp.beginPacket(HUB_IP, HUB_PORT);
  udp.write((const uint8_t*)buf, strlen(buf));
  udp.endPacket();
}

// Hub -> node commands: single ASCII char per packet.
//  'F' = faster (1 short pulse)  'S' = slower (2 pulses)  'R' = rest (long buzz)  'K' = kaalam change (3 pulses)
void handleCommands() {
  int n = udp.parsePacket();
  if (n <= 0) return;
  char c = udp.read();
  switch (c) {
    case 'F': pulse(80); break;
    case 'S': pulse(80); delay(120); pulse(80); break;
    case 'R': pulse(900); break;
    case 'K': for (int i = 0; i < 3; i++) { pulse(60); delay(100); } break;
    default: break;
  }
}

void loop() {
  uint32_t now = micros();
  if (now - lastSample >= SAMPLE_US) {
    lastSample = now;
    updateHeartRate();
    sendSample();
  }
  handleCommands();
  if (vibOffAt && millis() > vibOffAt) {
    digitalWrite(VIB_PIN, LOW); digitalWrite(LED_PIN, LOW); vibOffAt = 0;
  }
}
