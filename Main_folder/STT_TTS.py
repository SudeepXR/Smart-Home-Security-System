import sounddevice as sd
from scipy.io.wavfile import write
from faster_whisper import WhisperModel
import tempfile
import numpy as np

import pyttsx3
import requests
import json


WHISPER_MODEL = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)




def get_ai_response(prompt_text):
    url = "http://localhost:11434/api/chat"
    system_prompt = (
        "/no_think You are a friendly and polite interactive doorbell assistant. "
        "Follow these rules strictly:\n"
        "- Respond visitor based on the guidelines.\n"
        "- Also provide a hidden name for them based on what they say in the format [NAME:x].\n"
        "- Also provide a hidden suspicion score based on how suspicious their interaction is (0=low, 1=medium, 2=high) in the format [SUS:x].\n"
        "Assign this suspicion score based only on the clarity and consistency of the visitor's text: clear and specific = low, vague or incomplete = medium, agressive or demanding = high.”"
        "- If the visitor's purpose is related to a delivery, instruct them to leave the package at the front door.\n"
        "- If the visitor is a known guest, tell them to wait.\n"
        "- If unclear/stranger, say homeowner is unavailable.\n"
        "- If you cannot understand, ask them to repeat.\n"
        "- Append [END_CONVERSATION] if no further interaction is needed. Do not add [END_CONVERSATION] if you are asking a question back"
    )

    # data to send to the Ollama API
    data = {
        "model": "qwen3:8b",  
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt_text}
        ],
        "stream": False
    }

    try:
        response = requests.post(url, json=data)
        response.raise_for_status()

        response_json = response.json()
        if 'message' in response_json and 'content' in response_json['message']:
            return response_json['message']['content']
        else:
            return "I'm sorry, I couldn't generate a response."
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Ollama server: {e}")
        return "I'm sorry, I'm having trouble connecting to my assistant. Please try again later."


def speak(text):
    """Convert text to speech."""
    engine = pyttsx3.init()
    print(text)
    engine.say(text)
    engine.runAndWait()


def listen(duration=5, sample_rate=16000):
    """
    Record audio from mic and transcribe using Whisper
    """
    print("Listening... 🎤")

    recording = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="int16"
    )
    sd.wait()

    # Save temp wav
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        write(tmp.name, sample_rate, recording)
        wav_path = tmp.name

    try:
        segments, _ = WHISPER_MODEL.transcribe(
            wav_path,
            language="en",
            beam_size=5
        )

        text = " ".join(segment.text for segment in segments).strip()
        print("You said:", text)
        return text

    except Exception as e:
        print("Whisper STT error:", e)
        return ""



def run_conversation():
    """
    Run the STT <-> TTS conversation loop and return a tuple:
        (extracted_name_or_score, last_visitor_text)

    This function preserves the original behavior used when running the script
    as __main__ and returns the final values so other modules (like
    system_main.py) can import and call it directly to obtain the result.
    """
    conversation_active = True
    name = 0  # keep track of suspicion level / extracted NAME token
    last_visitor_text = ""

    speak("Hello, please tell me your name and reason for visiting.")

    while conversation_active:
        visitor_text = listen()

        # store last heard phrase even if empty
        last_visitor_text = visitor_text

        if visitor_text:
            ai_reply = get_ai_response(visitor_text)
            #print(ai_reply)
            # Extract suspicion score / hidden name token
            if "[NAME:" in ai_reply:
                try:
                    name_str = ai_reply.split("[NAME:")[1].split("]")[0]
                    name = name_str
                except Exception:
                    name = "Stranger"  # fallback
                ai_reply = ai_reply.replace(f"[NAME:{name}]", "").strip()

            if "[SUS:" in ai_reply:
                try:
                    sus_score_str = ai_reply.split("[SUS:")[1].split("]")[0]
                    sus_score = int(sus_score_str)
                except:
                    sus_score = 0  # fallback
                ai_reply = ai_reply.replace(f"[SUS:{sus_score}]", "").strip()           

            print(f"Name {name}")  # Only for homeowner

            # Check for the end conversation token
            if "[END_CONVERSATION]" in ai_reply:
                clean_reply = ai_reply.replace("[END_CONVERSATION]", "").strip()
                speak(clean_reply)
                conversation_active = False
            else:
                speak(ai_reply)
        else:
            speak("I didn't catch that. Could you please speak again?")

    # when finished, return extracted name and the last visitor text
    return name, last_visitor_text


# --- Demo Flow kept for backwards compatibility ---
if __name__ == "__main__":
    run_conversation()
