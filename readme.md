# Assistant Vocal TARS – Documentation - eSpeak

ATTENTION : Cette documentation parcours la réalisation d'un assistant vocal avec eSpeak sans Wek-word, plugins ou autre d'installés !


## 1. Introduction & Architecture

**Objectif**

Créer un assistant vocal “TARS” qui :

1. Écoute ta voix (micro local)
2. Transcrit le discours (STT local)
3. Envoie le texte à un serveur distant (VM AWS)
4. Le serveur traite la requête (logique + IA + personnalité)
5. Renvoie une réponse texte
6. Le client local lit la réponse à haute voix (TTS local)

```
[Micro / Haut-parleur]
       ⇅
[Client local (STT/TTS)]
       ⇅ HTTP
[Serveur VM (Flask + OpenAI)]

```

---

## 2. Prérequis

### 2.1 Matériel

- PC / Raspberry Pi / Eee PC (≥ 4 Go RAM conseillé)
- Microphone USB
- Haut-parleur USB ou jack
- Connexion Internet (pour VM & OpenAI)

### 2.2 Logiciels (local & serveur)

- Python 3.8+
- pip
- Vosk (STT local)
- eSpeak NG + pyttsx3 (TTS local)
- Flask + openai (serveur)

---

## 3. Partie Serveur “Cerveau” (VM AWS)

### 3.1 Mise en place sur la VM

```bash
# 1. Se connecter à la VM
ssh ubuntu@YOUR_VM_IP

# 2. Mettre à jour et installer Python
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip

# 3. Installer les bibliothèques
sudo apt install -y python3-flask
pip3 install --user openai

python3 - <<'EOF'
import flask, openai
print("Flask:", flask.__version__, "OpenAI:", openai.__version__)
EOF

# 4. Configurer la clé OpenAI
echo 'export OPENAI_API_KEY="sk-…"' >> ~/.bashrc
source ~/.bashrc

```

### 3.2 Scripts du serveur

### 3.2.1 `tars_personality.py`

```python
# tars_personality.py
"""
Définit la personnalité de TARS : réponses préconfigurées pour certaines requêtes
"""

PERSONALITY_RULES = [
    {
        "trigger_keywords": ["your name", "who are you"],
        "response": "I am TARS. Tactical Robot. Not your friend, but at your service."
    },
    {
        "trigger_keywords": ["mission", "purpose"],
        "response": "My mission is to assist you with unwavering efficiency and minimal sarcasm."
    },
    {
        "trigger_keywords": ["joke"],
        "response": "A neutron walks into a bar and asks, \"How much for a drink?\" The bartender replies, \"For you, no charge.\""
    }
]

def apply_personality(message: str) -> str:
    """
    Parcourt les règles et renvoie une réponse personnalisée si un mot-clé correspond.
    Sinon renvoie None.
    """
    text = message.lower()
    for rule in PERSONALITY_RULES:
        for kw in rule["trigger_keywords"]:
            if kw in text:
                return rule["response"]
    return None

```

### 3.2.2 `tars_brain_server.py`

```python
# tars_brain_server.py
from flask import Flask, request, jsonify
import os
from openai import OpenAI               # << importer OpenAI client
from tars_personality import apply_personality

app = Flask(__name__)

# Instancier le client avec ta clé
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route('/query', methods=['POST'])
def handle_query():
    data = request.get_json()
    user_text = data.get('text', '')

    # 1. Tenter une réponse selon la personnalité
    personality_response = apply_personality(user_text)
    if personality_response:
        return jsonify({"response": personality_response})

    # 2. Sinon, appel à la nouvelle interface chat.completions
    messages = [
        {"role": "system", "content": "You are TARS from Interstellar. Respond concisely and robotically."},
        {"role": "user",   "content": user_text}
    ]
    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",   # ou "gpt-4"
            messages=messages,
            max_tokens=150,
            temperature=0.7,
        )
        answer = resp.choices[0].message.content.strip()
    except Exception as e:
        answer = f"Error: {str(e)}"

    return jsonify({"response": answer})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

```

Crée `/etc/systemd/system/tars.service` :

```
[Unit]
Description=TARS Brain Server

[Service]
WorkingDirectory=/root
Environment="OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx"
ExecStart=/usr/bin/python3 tars_brain_server.py
Restart=always

[Install]
WantedBy=multi-user.target

```

```bash
sudo systemctl daemon-reload
sudo systemctl enable tars
sudo systemctl start tars

```

---

## 4. Partie Client Local (ton PC)

### 4.1 Installation & dépendances

```bash
sudo apt update
sudo apt install -y python3 python3-pip portaudio19-dev libatlas-base-dev sox libsox-fmt-all
pip3 install vosk sounddevice pyttsx3 requests

```

### 4.2 Télécharger le modèle Vosk

```bash
mkdir -p ~/models/vosk && cd ~/models/vosk
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip

```

### 4.3 `tars_local_client.py`

```python
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
VM_API_URL         = os.getenv('TARS_API_URL', 'http://18.215.143.5:5000/query')
VOSK_MODEL_PATH    = r"C:\vosk-model"    # Chemin sans accents vers ton modèle Vosk
SAMPLE_RATE        = 16000
RECOGNITION_TIMEOUT = 5                 # secondes max pour la reconnaissance
# ————————

# Initialisation TTS (pyttsx3 via SAPI Windows ou eSpeak NG)
tts = pyttsx3.init()
tts.setProperty('rate', 150)
voices = tts.getProperty('voices')
tts.setProperty('voice', voices[0].id)

def speak(text: str):
    """Ne lit à voix haute que la réponse de TARS."""
    print(f"TARS ▶ {text}")
    tts.say(text)
    tts.runAndWait()

# Initialisation Vosk STT
model = Model(VOSK_MODEL_PATH)
rec   = KaldiRecognizer(model, SAMPLE_RATE)
audio_q = queue.Queue()

def callback(indata, frames, time_info, status):
    if status:
        print(f"Audio status warning: {status}")
    audio_q.put(bytes(indata))

def recognize(timeout: float = RECOGNITION_TIMEOUT) -> str:
    """Transcrit l'audio pendant 'timeout' secondes."""
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
    with sd.RawInputStream(samplerate=SAMPLE_RATE,
                           blocksize=8000,
                           dtype='int16',
                           channels=1,
                           callback=callback):
        # Messages système affichés, non lus
        print("TARS ▶ System online.")
        while True:
            print("TARS ▶ Speak now.")
            text = recognize().strip().lower()
            print(f"You ▶ {text}")

            if not text:
                print("TARS ▶ I didn't catch that.")
                continue

            if any(cmd in text for cmd in ("exit","shutdown","goodbye","stop")):
                speak("Shutting down. Goodbye.")
                break

            # Envoi à la VM et récupération de la réponse
            try:
                resp = requests.post(VM_API_URL, json={'text': text}, timeout=5)
                resp.raise_for_status()
                answer = resp.json().get('response', '')
            except Exception as e:
                print(f"Error calling API: {e}")
                answer = "Error: cannot reach the server."

            # Seule la réponse de TARS est lue
            speak(answer)

if __name__ == '__main__':
    main()

```

### 4.4 Exécution

```bash
export TARS_API_URL="http://YOUR_VM_IP:5000/query"
python3 tars_local_client.py

```

Pour Windows :

Avec **WSL sous Windows 10**, tu es dans un cas un peu particulier : **WSL1 n’expose pas du tout les périphériques audio**, et WSL2 en expose à peine, mais il faut installer un **serveur PulseAudio** sous Windows pour que ta session Ubuntu voie quelque chose. Voici les deux voies possibles :

---

## Lancer le client Python **nativement sous Windows**

Tu as déjà un casque USB branché et fonctionnel sous Windows 10, donc le plus simple est de :

1. **Installer Python 3** (depuis le Microsoft Store ou python.org)
2. Ouvrir un PowerShell/cmd, installer tes dépendances :
    
    ```powershell
    pip install vosk sounddevice pyttsx3 requests
    
    ```
    
3. Télécharger et extraire le modèle Vosk dans un dossier (par exemple `C:\vosk-model-small-en-us-0.15`)
4. Copier `tars_local_client.py` sur Windows, et adapter la variable `VOSK_MODEL_PATH` à `C:\\vosk-model-small-en-us-0.15`
5. Dans le même shell :
    
    ```powershell
    set TARS_API_URL=http://13.220.82.24:5000/query
    python tars_local_client.py
    
    ```
    
6. Windows gérera **directement** ton casque USB pour l’entrée et la sortie audio, sans bidouille.

Jusqu’ici, l’asssistant vocal est fonctionnel. Il suffit de lancer le script local sur la machine cliente, et discuter avec l’assistant vocal.
