#include "SparkFun_SHTC3.h"
#include <WiFi.h>
#include <HTTPClient.h>

SHTC3 g_shtc3;

const char* ssid = "WIFI-DCI";
const char* password = "DComInf_2K24";
const char* serverUrl = "http://3.221.0.222:8081/data";

void errorDecoder(SHTC3_Status_TypeDef message) {
  switch (message) {
    case SHTC3_Status_Nominal:
      Serial.print("Nominal");
      break;
    case SHTC3_Status_Error:
      Serial.print("Error");
      break;
    case SHTC3_Status_CRC_Fail:
      Serial.print("CRC Fail");
      break;
    default:
      Serial.print("Unknown return code");
      break;
  }
}

void sendTemperature(float temp) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    String payload = "{\"device\":\"rak\", \"type\":\"temperature\", \"value\":" + String(temp, 1) + "}";

    int httpResponseCode = http.POST(payload);
    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.print("HTTP Response code: ");
      Serial.println(httpResponseCode);
      Serial.println("Server response: " + response);
    } else {
      Serial.print("Error on sending POST: ");
      Serial.println(httpResponseCode);
    }

    http.end();
  } else {
    Serial.println("WiFi not connected");
  }
}

void shtc3_read_data(void) {
  float Temperature = 0;

  g_shtc3.update();
  if (g_shtc3.lastStatus == SHTC3_Status_Nominal) {
    Temperature = g_shtc3.toDegC();
    Serial.print("T = ");
    Serial.print(Temperature);
    Serial.println(" °C");

    sendTemperature(Temperature);
  } else {
    Serial.print("Update failed, error: ");
    errorDecoder(g_shtc3.lastStatus);
    Serial.println();
  }
}

void setup() {
  Serial.begin(115200);
  delay(100);

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.println("WiFi connected");

  Wire.begin();
  Serial.print("Beginning sensor. Result = ");
  errorDecoder(g_shtc3.begin());
  Wire.setClock(400000);
  Serial.println();

  if (g_shtc3.passIDcrc) {
    Serial.print("ID Passed Checksum. Device ID: 0b");
    Serial.println(g_shtc3.ID, BIN);
  } else {
    Serial.println("ID Checksum Failed.");
  }
}

void loop() {
  shtc3_read_data();
  delay(5000);  // Intervalo de lectura y envío (ajustable)
}
