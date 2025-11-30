# MVJIT — Doorbell & Home Security Assistant

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

Frontend (code/)
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

Python services (Main/)
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
3. Run scripts:
   - Interactive demo: `python STT_TTS.py`
   - Orchestration server: `python server.py` or `python system_main.py`

Notes
- STT_TTS.py uses Google STT (`speech_recognition`) and `pyttsx3` for local TTS (blocking).
- Ensure external microphone is set as Windows default if used.
- The assistant expects an AI endpoint on `localhost:11434` by default; change `Main/STT_TTS.py` `get_ai_response` URL if needed.

## Environment, secrets & git
- Do NOT commit secrets or environment files (e.g., `.env`, `.env.local`).
- Add a `.env.example` with required variables and keep `.env` in `.gitignore`.
- Ignore: `node_modules/`, `.next/`, `.venv/`, `__pycache__/`, `*.pyc`, logs, and OS/IDE files.



