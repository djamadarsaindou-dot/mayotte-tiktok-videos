"""Génération du scénario via Groq (Llama)."""
import json
from groq import Groq

from src.config import GROQ_API_KEY, GROQ_MODEL


PROMPT_TEMPLATE = """{user_hint}

Réponds STRICTEMENT en JSON valide avec cette structure :
{{
  "title": "titre court et accrocheur (max 60 caractères)",
  "hook": "première phrase qui accroche en 1-2 secondes",
  "scenes": [
    {{
      "narration": "phrase de narration en français, claire, parlée à l'oral (12-25 mots)",
      "image_prompt": "description en ANGLAIS d'une image illustrant cette scène, style cinématique, vertical 9:16, sans texte, photoréaliste"
    }}
  ]
}}

Contraintes :
- Entre 5 et 7 scènes
- La somme des narrations doit faire environ 120-150 mots (≈ 50 secondes parlées)
- Chaque image_prompt doit être visuellement spécifique et concret
- N'inclus AUCUN texte hors du JSON, pas de markdown, pas d'explications
"""


def generate_script(topic_def: dict) -> dict:
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY manquante. Crée un compte gratuit sur https://console.groq.com/keys "
            "et ajoute la clé dans le fichier .env"
        )

    client = Groq(api_key=GROQ_API_KEY)
    user_prompt = PROMPT_TEMPLATE.format(user_hint=topic_def["user_hint"])

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": topic_def["system"]},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.9,
        response_format={"type": "json_object"},
        max_tokens=2000,
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)

    if not data.get("scenes") or not isinstance(data["scenes"], list):
        raise ValueError(f"Réponse Groq invalide : pas de scènes. Reçu : {raw[:300]}")

    return data
