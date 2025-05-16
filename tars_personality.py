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
