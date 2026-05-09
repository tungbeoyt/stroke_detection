# 🏥 NeuroHeart - Stroke Prediction & IoT System

Welcome to **NeuroHeart**! This is an intelligent system combining **IoT (Internet of Things)** and **AI (Artificial Intelligence)** to monitor cardiovascular health and predict stroke risks in real-time.

---

## 📚 1. System Overview
The system consists of 3 main components working together:
1.  **IoT Device (Hardware):** Measures heart rate and oxygen saturation (SpO2) from the patient and sends data to the Server.
2.  **Server & AI (The Brain):** Receives data, runs the AI model (XGBoost) to analyze risk factors.
3.  **Client (Web & Zalo):** Displays results and sends emergency alerts to relatives/doctors.

---

## 🛠 2. Prerequisites
Before starting, ensure your computer has the following tools:

### Basic Software
*   **Python (version 3.8+):** The main programming language.
    *   *Download:* [python.org](https://www.python.org/downloads/)
*   **VS Code:** Code editor.
*   **Git:** Version control tool (to download the project).

### Libraries & Auxiliary Tools
*   **Mosquitto MQTT:** Middleware to receive messages from sensors.
*   **Python Libraries (included in `requirements.txt`):**
    *   `Flask`: Runs the web server.
    *   `pandas`, `numpy`: Data processing.
    *   `xgboost`, `scikit-learn`: Runs the AI model.
    *   `paho-mqtt`: MQTT connection.

---

## 💻 3. Installation Guide (Localhost)
How to run the project on your personal computer.

### Step 1: Download Source Code
Open Terminal (or CMD/PowerShell) and run:
```bash
git clone https://github.com/Wangtran106/NeuroHeart_Project.git
cd NeuroHeart_Project
```

### Step 2: Create Virtual Environment
A virtual environment keeps libraries organized.
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux/Ubuntu
python3 -m venv venv
source venv/bin/activate
```
*(After running, you should see `(venv)` at the start of your Terminal line)*

### Step 3: Install Libraries (IMPORTANT)
Run the following command to automatically install all required libraries:
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Create a file named `.env` (with the dot at the beginning) and fill in the following parameters:
```ini
# MQTT Configuration (Use Localhost if running locally)
MQTT_BROKER=127.0.0.1
MQTT_PORT=1883
MQTT_USERNAME=wangtran
MQTT_PASSWORD=1006

# Web Configuration
FRONTEND_API_URL=http://127.0.0.1:5000
SECRET_KEY=your-secret-key
```

### Step 5: Run the Project
```bash
python app.py
```
If you see `Running on http://127.0.0.1:5000`, it is successful! Open your browser and visit that address.

---

## ☁️ 4.Real Server
To put the project online for public access.

## 🤖 5. Zalo Bot & Hardware
*   **Zalo Bot:** Code located in `zalo_module.py`. Get `ZALO_BOT_TOKEN` and add it to `.env`.
*   **Sensor (ESP32):** Hardware code (Arduino) needs to be flashed separately. 

---
**Author:** Tang Thanh Tung
**Contact:** tangtung17072004@gmail.com
# stroke_detection
