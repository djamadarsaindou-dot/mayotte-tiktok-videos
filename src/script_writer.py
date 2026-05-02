"""Génération du scénario via Groq (Llama).

Stratégie en 2 passes :
1. Llama propose un plan structuré (titre + 8 idées de scènes courtes)
2. Pour CHAQUE scène, on demande à Llama d'écrire EXACTEMENT 1 phrase de 20 mots
   (vérifiée et regénérée si hors-cible). Ça contourne la difficulté de Llama
   à respecter une longueur globale.
"""
import json
import re

from groq import Groq

from src.config import GROQ_API_KEY, GROQ_MODEL


PLAN_PROMPT = """{user_hint}

Propose le PLAN d'un mini-reportage TikTok de ~70 secondes.

Réponds STRICTEMENT en JSON :
{{
  "title": "titre court accrocheur (max 60 caractères)",
  "hook": "phrase d'accroche en 15-20 mots",
  "scenes": [
    {{
      "idea": "1 phrase courte décrivant l'idée de cette scène (10-15 mots)",
      "search_query": "2-4 mots-clés en ANGLAIS pour stock vidéo (ex: 'tropical lagoon aerial', 'coral reef fish')",
      "image_prompt": "description en ANGLAIS d'une scène cinématique vertical 9:16, photoréaliste"
    }}
  ]
}}

CONTRAINTES :
- EXACTEMENT 8 scènes
- Les 8 idées forment un récit cohérent et progressif (intro → développement → conclusion)
- search_query : visuel concret, facile à trouver en stock vidéo, pas de noms propres trop locaux
- Aucun texte hors du JSON
"""


EXPAND_PROMPT = """Réécris cette idée en UNE seule phrase complète, fluide et orale, EN FRANÇAIS.

Idée : {idea}
Contexte du reportage : {context}

CONTRAINTES STRICTES :
- EXACTEMENT entre 18 et 23 mots, pas un de moins
- Une seule phrase, pas deux
- Ton dynamique et narratif, comme un reportage TF1 ou Brut
- Pas de répétition avec les phrases précédentes
- Réponds avec UNIQUEMENT la phrase finale, sans guillemets, sans préfixe, sans explication

Phrase précédente (pour cohérence) : {prev_sentence}

Ta phrase :"""


WORD_RE = re.compile(r"\S+")


def _count_words(text: str) -> int:
    return len(WORD_RE.findall(text))


def _call_groq(client: Groq, system: str, user: str, json_mode: bool = False, temp: float = 0.85) -> str:
    kwargs = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temp,
        "max_tokens": 3000,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content.strip()


def _clean_sentence(s: str) -> str:
    s = s.strip().strip('"\'').strip()
    s = re.sub(r"^(Phrase|Réponse|Voici)\s*:\s*", "", s, flags=re.IGNORECASE)
    s = s.split("\n")[0].strip()
    return s


def _expand_scene(client: Groq, idea: str, context: str, prev: str) -> str:
    """Demande à Llama d'écrire une phrase de 18-23 mots. Retry si hors-cible."""
    for attempt in range(3):
        prompt = EXPAND_PROMPT.format(idea=idea, context=context, prev_sentence=prev or "(début)")
        sentence = _clean_sentence(
            _call_groq(client, "Tu es scénariste TikTok francophone.", prompt, temp=0.7 + attempt * 0.1)
        )
        wc = _count_words(sentence)
        if 17 <= wc <= 26:
            return sentence
        # Sinon on demande un ajustement
        if wc < 17:
            adjust = (
                f"La phrase suivante fait seulement {wc} mots, c'est trop court. "
                f"Réécris-la en l'enrichissant pour qu'elle fasse exactement entre 20 et 23 mots, "
                f"tout en gardant le sens. Réponds avec UNIQUEMENT la phrase enrichie.\n\n"
                f"Phrase : {sentence}"
            )
        else:
            adjust = (
                f"La phrase suivante fait {wc} mots, c'est trop long. "
                f"Réécris-la pour qu'elle fasse exactement entre 20 et 23 mots, "
                f"sans perdre le sens. Réponds avec UNIQUEMENT la phrase ajustée.\n\n"
                f"Phrase : {sentence}"
            )
        sentence2 = _clean_sentence(
            _call_groq(client, "Tu es scénariste TikTok francophone.", adjust, temp=0.5)
        )
        if 17 <= _count_words(sentence2) <= 26:
            return sentence2
    return sentence  # dernier recours


def generate_script(topic_def: dict) -> dict:
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY manquante. Crée un compte sur https://console.groq.com/keys "
            "et ajoute la clé dans le fichier .env"
        )

    client = Groq(api_key=GROQ_API_KEY)

    plan_user = PLAN_PROMPT.format(user_hint=topic_def["user_hint"])
    plan_raw = _call_groq(client, topic_def["system"], plan_user, json_mode=True)
    plan = json.loads(plan_raw)

    if not plan.get("scenes") or not isinstance(plan["scenes"], list):
        raise ValueError("Pas de plan généré")

    plan["scenes"] = plan["scenes"][:8]
    while len(plan["scenes"]) < 8:
        plan["scenes"].append({
            "idea": f"Conclusion sur {topic_def['label']}",
            "search_query": "tropical island sunset",
            "image_prompt": "tropical island at sunset, cinematic, vertical 9:16",
        })

    print(f"   Plan : {plan.get('title', '?')} ({len(plan['scenes'])} scènes)")

    context = f"Sujet : {topic_def['label']}. Titre : {plan.get('title', '')}"
    final_scenes: list[dict] = []
    prev_sentence = plan.get("hook", "")

    for i, scene in enumerate(plan["scenes"]):
        idea = scene.get("idea", "")
        narration = _expand_scene(client, idea, context, prev_sentence)
        wc = _count_words(narration)
        print(f"   Scène {i+1} : {wc} mots → {narration[:60]}...")
        final_scenes.append({
            "narration": narration,
            "search_query": scene.get("search_query", idea),
            "image_prompt": scene.get("image_prompt", idea),
        })
        prev_sentence = narration

    total = sum(_count_words(s["narration"]) for s in final_scenes)
    print(f"   📊 Total : {total} mots (cible 145-185, ≈ {total*0.42:.0f}s parlés)")

    return {
        "title": plan.get("title", topic_def["label"]),
        "hook": plan.get("hook", ""),
        "scenes": final_scenes,
    }
