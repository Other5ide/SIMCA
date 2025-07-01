#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>

// Configuración del sensor DHT
#define DHTPIN 4         // Pin al que está conectado el sensor
#define DHTTYPE DHT22    // Puede ser DHT11 o DHT22
DHT dht(DHTPIN, DHTTYPE);

// Datos de WiFi
// Cambia estos datos por los de tu red WiFi
const char* ssid = "WIFI-DCI";
const char* password = "DComInf_2K24";

// URL del servidor REST
const char* serverUrl = "http://3.221.0.222:8081/data";

void setup() {
  Serial.begin(115200);
  dht.begin();

  // Conectar a WiFi
  WiFi.begin(ssid, password);
  Serial.print("Conectando a WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConectado a WiFi!");
}

bool send_data(String s1) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    if (http.begin(serverUrl)) {
      http.addHeader("Content-Type", "application/json");

      Serial.print("Enviando: ");
      Serial.println(s1);

      int httpResponseCode = http.POST(s1);
      if (httpResponseCode == 200) {
        Serial.println("POST exitoso");
        http.end();
        return true;
      } else {
        Serial.print("Error en POST, código: ");
        Serial.println(httpResponseCode);
        http.end();
        return false;
      }
    } else {
      Serial.println("Error al iniciar conexión HTTP");
      return false;
    }
  } else {
    Serial.println("WiFi no conectado");
    return false;
  }
}

void loop() {
  float temp = dht.readTemperature();  // Leer temperatura en °C

  if (isnan(temp)) {
    Serial.println("Error al leer temperatura");
  } else {
    // Crear el payload JSON
    String jsonPayload = "{\"device\":\"rak\", \"type\":\"temperature\", \"value\":" + String(temp, 1) + "}";
    send_data(jsonPayload);
  }

  delay(10000); // Esperar 10 segundos
}
