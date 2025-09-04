#include "esp_camera.h"
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <UniversalTelegramBot.h>

#define CAMERA_MODEL_AI_THINKER
#include "camera_pins.h"

// Replace with your network credentials
const char* ssid = "わたしも大好き";
const char* password = "151229122105";

// Initialize Telegram BOT
#define BOTtoken "7722026656:AAFQaefBhnO3iO5_1AkE6DTpB7jecKoIjFk" // Your bot token
#define CHAT_ID "344319931" // Your chat ID

WiFiClientSecure client;
UniversalTelegramBot bot(BOTtoken, client);

void startCameraServer();
void sendPhotoTelegram();

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_SVGA;  // Adjusted for faster capture and smaller image
  config.jpeg_quality = 12;            // Lower quality = smaller file
  config.fb_count = 2;

  // Camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  sensor_t * s = esp_camera_sensor_get();
  s->set_framesize(s, FRAMESIZE_SVGA);
  s->set_brightness(s, 1);
  s->set_contrast(s, 1);
  s->set_saturation(s, 1);
  s->set_gainceiling(s, (gainceiling_t)3);

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");

  client.setInsecure();

  // Start camera server (optional, unused here)
  startCameraServer();
}

void loop() {
  sendPhotoTelegram();
  delay(60000); // wait 60 seconds
}

void sendPhotoTelegram() {
  camera_fb_t * fb = NULL;
  fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed");
    return;
  }

  Serial.println("Connecting to Telegram server...");
  if (client.connect("api.telegram.org", 443)) {
    String getAll = "";
    String getBody = "";
    String token = BOTtoken;
    String chat_id = CHAT_ID;

    String serverName = "/bot" + token + "/sendPhoto";
    
    // Added caption here
    String caption = "Movement Detected with low Scale!!";  

    String head = "--BOUNDARY\r\n"
                  "Content-Disposition: form-data; name=\"chat_id\"\r\n\r\n" + chat_id + 
                  "\r\n--BOUNDARY\r\n"
                  "Content-Disposition: form-data; name=\"caption\"\r\n\r\n" + caption + 
                  "\r\n--BOUNDARY\r\n"
                  "Content-Disposition: form-data; name=\"photo\"; filename=\"photo.jpg\"\r\n"
                  "Content-Type: image/jpeg\r\n\r\n";
    String tail = "\r\n--BOUNDARY--\r\n";

    uint16_t imageLen = fb->len;
    uint16_t extraLen = head.length() + tail.length();
    uint16_t totalLen = imageLen + extraLen;

    client.println("POST " + serverName + " HTTP/1.1");
    client.println("Host: api.telegram.org");
    client.println("Content-Length: " + String(totalLen));
    client.println("Content-Type: multipart/form-data; boundary=BOUNDARY");
    client.println();
    client.print(head);

    uint8_t *fbBuf = fb->buf;
    size_t fbLen = fb->len;
    for (size_t n = 0; n < fbLen; n = n + 1024) {
      if (n + 1024 < fbLen) {
        client.write(fbBuf, 1024);
        fbBuf += 1024;
      } else if (fbLen % 1024 > 0) {
        size_t remainder = fbLen % 1024;
        client.write(fbBuf, remainder);
      }
    }
    client.print(tail);

    int timoutTimer = 10000;
    long startTimer = millis();
    boolean state = false;

    while ((startTimer + timoutTimer) > millis()) {
      Serial.print(".");
      delay(100);
      while (client.available()) {
        char c = client.read();
        if (c == '\n') {
          if (getAll.length() == 0) state = true;
          getAll = "";
        } else if (c != '\r') {
          getAll += String(c);
        }
        if (state == true) getBody += String(c);
        startTimer = millis();
      }
      if (getBody.length() > 0) break;
    }
    client.stop();
    Serial.println(getBody);
  }
  esp_camera_fb_return(fb);
}
