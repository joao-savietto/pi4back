#include "ESP32SensorAPI.h"

// Constructor
ESP32SensorAPI::ESP32SensorAPI(const char* url) {
    this->serverUrl = String(url);
    this->authToken = "";
    this->isAuthenticated = false;
}

// Set server URL
void ESP32SensorAPI::setServerUrl(const char* url) {
    this->serverUrl = String(url);
}

// Authenticate user with username and password
bool ESP32SensorAPI::authenticate(const String& username, const String& password) {
    // Check if WiFi is connected
    if (WiFi.status() != WL_CONNECTED) {
        return false;
    }

    HTTPClient http;
    http.begin(serverUrl + "/auth/login");
    http.addHeader("Content-Type", "application/json");

    // Create JSON payload for login request
    String jsonPayload = "{\"username\":\"" + username + "\",\"password\":\"" + password + "\"}";

    int httpResponseCode = http.POST(jsonPayload);

    if (httpResponseCode > 0) {
        String response = http.getString();
        
        // Parse JSON response
        DynamicJsonDocument doc(1024);
        DeserializationError error = deserializeJson(doc, response);
        
        if (!error) {
            // Check if access_token exists in response
            if (doc.containsKey("access_token")) {
                this->authToken = doc["access_token"].as<String>();
                this->isAuthenticated = true;
                http.end();
                return true;
            }
        }
    }

    this->isAuthenticated = false;
    http.end();
    return false;
}

// Send measurement data to API
bool ESP32SensorAPI::sendMeasurement(float temperature, float humidity) {
    // Check if authenticated
    if (!this->isAuthenticated) {
        return false;
    }

    // Check if WiFi is connected
    if (WiFi.status() != WL_CONNECTED) {
        return false;
    }

    HTTPClient http;
    http.begin(serverUrl + "/measurements/");
    http.addHeader("Content-Type", "application/json");
    http.addHeader("Authorization", "Bearer " + this->authToken);

    // Create JSON payload for measurement
    String jsonPayload = "{\"temperature\":" + String(temperature) + 
                        ",\"humidity\":" + String(humidity) + "}";  

    int httpResponseCode = http.POST(jsonPayload);

    if (httpResponseCode > 0) {
        String response = http.getString();
        http.end();
        return true;
    }

    http.end();
    return false;
}

// Check authentication status
bool ESP32SensorAPI::isAuthenticatedUser() {
    return this->isAuthenticated;
}

// Get current auth token
String ESP32SensorAPI::getAuthToken() {
    return this->authToken;
}
