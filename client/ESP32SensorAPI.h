#ifndef ESP32_SENSOR_API_H
#define ESP32_SENSOR_API_H

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

class ESP32SensorAPI {
private:
    String serverUrl;
    String authToken;
    bool isAuthenticated;

public:
    /**
     * Constructor for ESP32SensorAPI class
     * @param url Base URL of the FastAPI server (e.g., "http://your-server-ip:8000")
     */
    ESP32SensorAPI(const char* url);

    /**
     * Authenticate user with username and password
     * @param username User's username
     * @param password User's password
     * @return True if authentication successful, false otherwise
     */
    bool authenticate(const String& username, const String& password);

    /**
     * Send temperature and humidity measurements to the API
     * @param temperature Temperature value in Celsius
     * @param humidity Humidity percentage value
     * @return True if successfully sent, false otherwise
     */
    bool sendMeasurement(float temperature, float humidity);

    /**
     * Set server URL (can be called to change server address)
     * @param url New server URL
     */
    void setServerUrl(const char* url);

    /**
     * Check if currently authenticated
     * @return True if authenticated, false otherwise
     */
    bool isAuthenticatedUser();

    /**
     * Get the current authentication token
     * @return Current JWT token or empty string if not authenticated
     */
    String getAuthToken();
};

#endif // ESP32_SENSOR_API_H
