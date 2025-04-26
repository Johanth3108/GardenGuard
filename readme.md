# 🌱 Smart Garden Dashboard

Real-time wireless monitoring and AI-powered gardening advice!  
This project connects an ESP32-based soil sensor to a Flask web app, displays garden health in real time, and uses Google Gemini AI to speak with your garden. 🌿

---

## 🚀 Features

- **BLE (Bluetooth Low Energy) communication** with ESP32
- **Live sensor updates** every 5 seconds
- **Gemini AI recommendations** generated every 15 seconds
- **Automatic CSV logging** of sensor data and AI responses
- **Live web dashboard** showing plant health and smart suggestions

---

## 📂 Project Structure

```plaintext
.
├── app.py              # Main Python server
├── data.csv            # Sensor data log (auto-created)
├── gemini_data.csv     # Gemini AI response log (auto-created)
├── templates/
│   └── index.html      # Frontend HTML
└── static/
    └── script.js       # Frontend JavaScript

