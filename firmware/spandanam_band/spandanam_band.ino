// Spandanam — wearable haptic band. Board: Seeed XIAO ESP32-S3.
// 8 vibration motors on PWM via ULN2003 / TB6612 driver. Hub sends frames over Wi-Fi UDP.
// Frame format (binary, 9 bytes): 'S' + 8 intensity bytes (0-255), one per motor. Timeout -> all off.
#include <WiFi.h>
#include <WiFiUdp.h>
#include "config.h"

// Body map (index -> motor):
// 0 chest  1 back  2 L wrist  3 R wrist  4 L shoulder  5 R shoulder  6 L finger  7 R finger
constexpr int MOTOR_PINS[8] = {1, 2, 3, 4, 5, 6, 7, 8};
constexpr int PWM_FREQ = 20000, PWM_BITS = 8;
constexpr uint32_t FRAME_TIMEOUT_MS = 300;

WiFiUDP udp;
uint32_t lastFrame = 0;

void allOff() { for (int i = 0; i < 8; i++) ledcWrite(i, 0); }

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < 8; i++) { ledcSetup(i, PWM_FREQ, PWM_BITS); ledcAttachPin(MOTOR_PINS[i], i); }
  WiFi.mode(WIFI_STA); WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) { delay(200); Serial.print("."); }
  udp.begin(BAND_PORT);
  Serial.printf("\nband up at %s\n", WiFi.localIP().toString().c_str());
  // hello pulse: chest then wrists
  ledcWrite(0, 200); delay(150); ledcWrite(0, 0); ledcWrite(2, 200); ledcWrite(3, 200); delay(150); allOff();
}

void loop() {
  int n = udp.parsePacket();
  if (n >= 9) {
    uint8_t buf[9]; udp.read(buf, 9);
    if (buf[0] == 'S') { for (int i = 0; i < 8; i++) ledcWrite(i, buf[i + 1]); lastFrame = millis(); }
  }
  if (millis() - lastFrame > FRAME_TIMEOUT_MS) allOff();
}
