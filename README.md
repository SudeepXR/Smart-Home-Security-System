# SecureHome

SecureHome is an **AI-powered smart home security system** designed to go beyond traditional CCTV and doorbell solutions.  
Instead of just recording footage, SecureHome actively **understands what is happening**, **interacts with visitors**, and **assists homeowners in real time** using computer vision, speech interfaces, and an AI assistant.

The system is built as a **lightweight, distributed, multi-device architecture**, making it suitable for real-world deployment using common hardware such as webcams, microphones, speakers, and ESP-based IoT devices.

## What SecureHome Does

- 📹 **Live surveillance & human detection** using on-device computer vision  
- 🧠 **Face recognition** to distinguish known vs unknown visitors  
- 🎙️ **Two-way voice interaction** with visitors using Speech-to-Text (STT) and Text-to-Speech (TTS)  
- 🤖 **Local AI assistant** for intelligent responses, system control, and query handling  
- 📊 **Web dashboard** for monitoring system status, live feed, logs, and alerts  
- 📁 **Persistent visitor logging** using a lightweight SQLite database  
- 🔌 **IoT integration** (ESP8266) for doorbell input, LEDs, and physical alerts  

## Operating Modes

SecureHome supports **three distinct operating modes**, allowing the system to adapt its behavior based on the home’s current needs:

### 1️⃣ Normal Mode  
- Standard security monitoring  
- Detects visitors, performs face recognition, and logs activity  
- Allows manual interaction through the dashboard and AI assistant  

### 2️⃣ Child Safety Mode  
- Designed for homes with children  
- Notifies parents when the door is opened/closed with an alert when the door is opened for extended periods of time.  
- Triggers **stricter monitoring** and **faster alerts**  
- Prioritizes unknown-person detection and abnormal activity  
- Reduces reliance on manual confirmation  
- Integrates with the **ESP8266 module** 

### 3️⃣ Presence Simulator Mode  
- Used when homeowners are **away from home**  
- Integrates with the **ESP8266 module**  
- Simulates human presence by:
  - Controlling LEDs and connected devices
  - Responding to doorbell interactions
- Helps deter potential intruders by making the house appear occupied

## Why SecureHome Is Different

Most smart security systems are **passive** — they record video and notify users.  
SecureHome is **active and intelligent**:

- It understands **who** is at the door
- It can **talk back** to visitors
- It can **log, reason, and assist** instead of just streaming video
- It is **privacy-first**, running AI and vision models locally without cloud dependency

## System Architecture (High Level)

SecureHome runs across **three coordinated systems**:

1. **Frontend System**  
   - Next.js dashboard for live feed, system state, logs, and controls  

2. **Backend / AI System**  
   - Python services handling:
     - Face recognition
     - Speech recognition & synthesis
     - AI assistant orchestration
     - Database logging
     - Security logic  

3. **CCTV / Vision System**  
   - Dedicated camera service for live video capture and detection  

An optional **ESP8266 device** acts as the physical interface for doorbell presses and alerts.

---


Lightweight multi-component project combining:
- A Next.js dashboard and UI (frontend) in `code/`
- Python on-device assistant, STT/TTS, face recognition and orchestration in `Main/` and `Face/`
- A small SQLite-backed DB (`Main/database/`)

## Repository layout
- `code/` — Next.js app (TypeScript, components, API routes)
- `Main/` — Python scripts (STT_TTS.py, system_main.py, server.py, etc.)
- `Face/` — face encoding and recognition utilities
- `Main/database/` — sqlite helper, models, init scripts

## Quick start

Prerequisites
- Node 18+ and pnpm (or npm)
- Python 3.9+
- On Windows: microphone permissions for STT and sound for TTS
- Local Ollama-compatible assistant at `http://localhost:11434/api/chat` if using the AI backend

### Frontend (code/) (run on 1st device)
1. Open terminal in `code/`
2. Install and run:
   - pnpm:
     ```
     pnpm install
     pnpm run dev
     ```
   - or npm:
     ```
     npm install
     npm run dev
     ```
3. Visit the configured port (default 3000). 


### Python services (Main_folder/ and Face/) (run on 2nd device)
1. Create and activate a virtual environment:
   ```
   cd Main
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1   # PowerShell on Windows
   ```
2. Install packages (create `requirements.txt` if not present):
   ```
   pip install speechrecognition pyttsx3 requests opencv-python
   ```
   and other required packages

3. Run scripts:
   - Interactive demo: `python system_main.py`
   - Orchestration backend server: `python app.py`

### CCTV camera services (Main_folder/CCTV) (run on 3rd device)
1. Create and activate a virtual environment:
   ```
   cd Main
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1   # PowerShell on Windows
   ```
2. Install packages (create `requirements.txt` if not present):
   ```
   pip install opencv-python requests ultralytics
   ```
3. Run scripts:`app.py`

### ESP (door_ESP8266.ino) 
- Connect LED's and button to required pins
- Use Arduino IDE to open and flash `door_ESP8266.ino` (path depends on your project layout).
- Configure Wi‑Fi and server endpoint in the sketch.

## Configuration & Environment
- Frontend env: `code/.env.local`
- Backend env: `Final_Backend/HTFBack/Main_folder/.env` (create if missing)
- DB: SQLite files live under `Final_Backend/HTFBack/Main_folder/database/`; migrations/initialization scripts are in the same folder.


Notes
- STT_TTS.py uses `faster_whisper` and `pyttsx3` for local STT-TTS.
- Ensure external microphone is set as Windows default if used.
- Camera Sources should be changed to 0 if webcam is user
- The assistant expects an AI endpoint on `localhost:11434` by default; change `Main/STT_TTS.py` `get_ai_response` URL if needed.
- Configure all IP addresses for the 3 systems (IP_SUD for backend, IP_MEG for CCTV, IP_SUT for frontend system, IP_ESP for ESP8266
