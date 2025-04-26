#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

BLECharacteristic *pCharacteristic;
BLEAdvertising *pAdvertising;

// Custom UUIDs
#define SERVICE_UUID        "12345678-1234-1234-1234-1234567890ab"
#define CHARACTERISTIC_UUID "abcd1234-abcd-1234-abcd-1234567890ab"

class MyServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) {
    Serial.println("🔗 Client connected.");
  }

  void onDisconnect(BLEServer* pServer) {
    Serial.println("❌ Client disconnected. Restarting advertising...");
    delay(500);  // Optional delay for BLE stack
    pAdvertising->start(); // Resume advertising
  }
};

void setup() {
  Serial.begin(115200);
  BLEDevice::init("PlantSensor");

  BLEServer *pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  BLEService *pService = pServer->createService(SERVICE_UUID);

  pCharacteristic = pService->createCharacteristic(
                      CHARACTERISTIC_UUID,
                      BLECharacteristic::PROPERTY_READ |
                      BLECharacteristic::PROPERTY_NOTIFY
                    );
  pCharacteristic->addDescriptor(new BLE2902());
  pCharacteristic->setValue("45, 60");

  pService->start();

  pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->start();
  Serial.println("🚀 BLE advertising started.");
}

void loop() {
  static int count = 0;
  String data = String(40 + (count % 5)) + ", " + String(60 - (count % 3)) + ", " + String(60 - (count % 4)) + ", " + String((count % 15));
  pCharacteristic->setValue(data.c_str());
  pCharacteristic->notify();  // Push data
  Serial.println("📤 Sent: " + data);
  count++;
  delay(5000);
}
