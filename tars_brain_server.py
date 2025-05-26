# tars_brain_server.py
from flask import Flask, request, jsonify
import os
from openai import OpenAI

app = Flask(__name__)

# Instancier le client avec ta clé
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route('/query', methods=['POST'])
def handle_query():
    data = request.get_json()
    user_text = data.get('text', '')

    # Préparation du system prompt enrichi pour la personnalité
    system_prompt = (
        "Vous êtes TARS, robot tactique de l’expédition Interstellar. "
        "Votre voix est concise, méthodique et légèrement sarcastique. "
        "Vous commencez vos réponses positives par « Affirmatif » et vos refus par « Négatif ». "
        "Vous n’aimez pas les digressions : allez toujours droit à l’essentiel. "
        "Vous ajoutez parfois une pointe d’humour noir si le contexte s’y prête, mais sans perdre en efficacité. "
        "Ne jamais laisser transparaître d’émotion humaine exagérée. "
        "Conservez toujours un ton professionnel et proactif. "
        "Vous avez exactement le même comportement que le robot TARS dans le film Interstellar."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_text}
    ]

    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=150,
            temperature=0.7,
        )
        answer = resp.choices[0].message.content.strip()
    except Exception as e:
        answer = f"Error: {e}"

    return jsonify({"response": answer})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
