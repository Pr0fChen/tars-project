# tars_local_client.py
import os
import queue
import requests
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import json
import pyttsx3
import time

# — CONFIGURATION —
VM_API_URL = os.getenv('TARS_API_URL', 'http://13.220.82.24:5000/query')
VOSK_MODEL_PATH = r"C:\vosk-model"       # Chemin sans accents vers ton modèle Vosk
SAMPLE_RATE = 16000
RECOGNITION_TIMEOUT = 5  # secondes
# ————————

# Initialisation TTS (pyttsx3 via SAPI Windows ou eSpeak NG)
tts = pyttsx3.init()
tts.setProperty('rate', 150)
voices = tts.getProperty('voices')
tts.setProperty('voice', voices[0].id)

def speak(text: str):
    print(f"TARS ▶ {text}")
    tts.say(text)
    tts.runAndWait()

# Initialisation Vosk STT
model = Model(VOSK_MODEL_PATH)
rec = KaldiRecognizer(model, SAMPLE_RATE)
audio_q = queue.Queue()

def callback(indata, frames, time_info, status):
    if status:
        print(f"Audio status warning: {status}")
    audio_q.put(bytes(indata))

def recognize(timeout: float = RECOGNITION_TIMEOUT) -> str:
    rec.AcceptWaveform(b"")
    end_time = time.time() + timeout
    text = ""
    while time.time() < end_time:
        try:
            data = audio_q.get(timeout=0.5)
        except queue.Empty:
            continue
        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
            text = res.get('text', '')
            break
    if not text:
        res = json.loads(rec.FinalResult())
        text = res.get('text', '')
    return text

def main():
    try:
        with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000,
                               dtype='int16', channels=1, callback=callback):
            speak("System online. Speak now.")
            while True:
                text = recognize().strip().lower()
                print(f"You ▶ {text}")
                if not text:
                    speak("I didn't catch that.")
                    continue
                if any(cmd in text for cmd in ("exit","shutdown","goodbye","stop")):
                    speak("Shutting down. Goodbye.")
                    break
                try:
                    resp = requests.post(VM_API_URL, json={'text': text}, timeout=5)
                    resp.raise_for_status()
                    answer = resp.json().get('response', '')
                except Exception as e:
                    print(f"Error calling API: {e}")
                    answer = "Error: cannot reach the server."
                speak(answer)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Fatal error: {e}")

if __name__ == '__main__':
    main()
