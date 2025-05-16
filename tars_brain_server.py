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
