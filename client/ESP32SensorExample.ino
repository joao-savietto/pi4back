/**
 * ESP32 Sensor API Usage Example
 * 
 * This example demonstrates how to use the ESP32SensorAPI class
 * to authenticate with your FastAPI server and send sensor data.
 */

#include <WiFi.h>
#include "ESP32SensorAPI.h"

// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Your API server address (change this to your actual server IP)
const char* serverUrl = "http://192.168.1.100:8000";  // Change to your server's IP and port

// API credentials
const String username = "admin";    // Change to your admin username
const String password = "password123";  // Change to your admin password

// Create sensor API instance
ESP32SensorAPI sensorAPI(serverUrl);

void setup() {
    Serial.begin(115200);
    
    // Connect to WiFi
    WiFi.begin(ssid, password);
    Serial.print("Connecting to WiFi");
    
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    
    Serial.println();
    Serial.println("Connected to WiFi network");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    
    // Authenticate with the API server
    Serial.println("Authenticating with API server...");
    if (sensorAPI.authenticate(username, password)) {
        Serial.println("Authentication successful!");
    } else {
        Serial.println("Authentication failed!");
        return;
    }
}

void loop() {
    // Simulate sensor readings (replace with actual sensor code)
    float temperature = 25.5;  // Example temperature
    float humidity = 60.2;   // Example humidity
    
    Serial.print("Sending measurement - Temp: ");
    Serial.print(temperature);
    Serial.print("°C, Humidity: ");
    Serial.print(humidity);
    Serial.println("%");
    
    // Send measurements to API server
    if (sensorAPI.sendMeasurement(temperature, humidity)) {
        Serial.println("Measurement sent successfully!");
    } else {
        Serial.println("Failed to send measurement!");
    }
    
    // Wait before next reading
    delay(10000);  // Send every 10 seconds
}
