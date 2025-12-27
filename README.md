# SecureHome

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





