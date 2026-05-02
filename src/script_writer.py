"""Génération de scénarios longs (2min+) en 2 passes.

Pass 1 — Plan : 16 scènes avec idée + 3 visuels distincts
Pass 2 — Pour chaque scène, expansion forcée à 22-28 mots, terminée par un point
"""
import json
import re

from groq import Groq

from src.config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    NUM_SCENES,
    TARGET_WORDS_MAX,
    TARGET_WORDS_MIN,
    VISUALS_PER_SCENE,
)

PLAN_PROMPT = """{user_hint}

Propose le plan détaillé d'un mini-reportage TikTok de 2 à 2 minutes 30, format vertical.

Réponds STRICTEMENT en JSON :
{{
  "title": "titre court accrocheur (max 60 caractères)",
  "hook": "phrase d'accroche en 15-22 mots",
  "scenes": [
    {{
      "idea": "1 phrase d'idée pour cette scène (12-18 mots)",
      "visuals": [
        "mots-clés en ANGLAIS pour stock vidéo, visuel 1 (ex: 'aerial tropical lagoon')",
        "mots-clés en ANGLAIS, visuel 2 (différent du 1, ex: 'fisherman boat sunset')",
        "mots-clés en ANGLAIS, visuel 3 (différent des autres, ex: 'underwater coral fish')"
      ],
      "image_prompt": "description en ANGLAIS d'une scène cinématique vertical 9:16, photoréaliste (utilisée si stock vidéo échoue)"
    }}
  ]
}}

CONTRAINTES STRICTES :
- EXACTEMENT {n_scenes} scènes (c'est crucial pour atteindre 2 minutes)
- Les {n_scenes} idées forment un récit structuré : intro accrocheuse, développement progressif (contexte, exemples, anecdotes, témoignages, données), conclusion mémorable
- Chaque scène a EXACTEMENT 3 visuels distincts (3 angles visuels différents pour la même idée)
- Les visuels doivent être faciles à trouver en stock vidéo : paysages, métiers, animaux, lieux, ambiance, gestes
- Pas de noms propres trop spécifiques dans les visuels (préfère "tropical island lagoon" à "Petite-Terre Mayotte")
- Les visuels doivent montrer une variété d'ECHELLES : large/aérien, moyen/personnage, gros plan/détail
- Aucun texte hors du JSON
"""

EXPAND_SYSTEM = "Tu es scénariste TikTok francophone, ton dynamique et narratif comme un reportage Brut ou TF1."

EXPAND_PROMPT = """Réécris cette idée en UNE phrase complète, fluide et orale, en français.

Idée : {idea}
Contexte du reportage : {context}
Phrase précédente (pour cohérence narrative) : {prev}

CONTRAINTES NON-NÉGOCIABLES :
- EXACTEMENT entre 22 et 28 mots
- UNE seule phrase
- DOIT se terminer par un point « . » (très important pour les pauses orales)
- Style oral fluide, sujet + verbe + complément clair
- Pas de répétition avec la phrase précédente
- Évite les listes ou énumérations à virgules en cascade
- Réponds avec UNIQUEMENT la phrase, sans guillemets ni préfixe

Ta phrase :"""

WORD_RE = re.compile(r"\S+")


def _wc(text: str) -> int:
    return len(WORD_RE.findall(text))


def _ensure_period(text: str) -> str:
    text = text.strip().rstrip(",;:")
    if text and text[-1] not in ".!?":
        text += "."
    return text


def _clean_sentence(s: str) -> str:
    s = s.strip().strip('"\'').strip()
    s = re.sub(r"^(Phrase|R[ée]ponse|Voici|Phrase finale)\s*:?\s*", "", s, flags=re.IGNORECASE)
    s = s.split("\n")[0].strip()
    return _ensure_period(s)


def _call_groq(client: Groq, system: str, user: str, json_mode: bool = False, temp: float = 0.85) -> str:
    kwargs = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temp,
        "max_tokens": 4000,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    return client.chat.completions.create(**kwargs).choices[0].message.content.strip()


def _expand(client: Groq, idea: str, context: str, prev: str) -> str:
    """Expanse une idée en une phrase de 22-28 mots, terminée par un point."""
    for attempt in range(3):
        prompt = EXPAND_PROMPT.format(idea=idea, context=context, prev=prev or "(début)")
        sentence = _clean_sentence(_call_groq(client, EXPAND_SYSTEM, prompt, temp=0.7 + attempt * 0.1))
        wc = _wc(sentence)
        if 20 <= wc <= 30:
            return sentence
        if wc < 20:
            adjust = (
                f"La phrase fait {wc} mots, c'est trop court. Réécris-la en l'enrichissant "
                f"pour qu'elle fasse exactement entre 23 et 27 mots, en gardant le sens. "
                f"Termine par un point. Réponds avec UNIQUEMENT la phrase.\n\nPhrase : {sentence}"
            )
        else:
            adjust = (
                f"La phrase fait {wc} mots, c'est trop long. Réécris-la pour qu'elle fasse "
                f"exactement entre 23 et 27 mots, sans perdre le sens. Termine par un point. "
                f"Réponds avec UNIQUEMENT la phrase.\n\nPhrase : {sentence}"
            )
        sentence2 = _clean_sentence(_call_groq(client, EXPAND_SYSTEM, adjust, temp=0.5))
        if 20 <= _wc(sentence2) <= 30:
            return sentence2
    return sentence


def _normalize_plan(plan: dict, topic_label: str) -> dict:
    scenes = plan.get("scenes", [])[:NUM_SCENES]
    while len(scenes) < NUM_SCENES:
        scenes.append({
            "idea": f"Conclusion sur {topic_label}",
            "visuals": ["tropical island sunset", "ocean waves shore", "palm trees beach"],
            "image_prompt": "tropical island at sunset, cinematic, vertical 9:16, photorealistic",
        })
    for s in scenes:
        visuals = s.get("visuals") or []
        if isinstance(visuals, str):
            visuals = [visuals]
        while len(visuals) < VISUALS_PER_SCENE:
            visuals.append(s.get("idea", topic_label))
        s["visuals"] = visuals[:VISUALS_PER_SCENE]
    plan["scenes"] = scenes
    return plan


def generate_script(topic_def: dict) -> dict:
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY manquante. https://console.groq.com/keys → mettre dans .env"
        )

    client = Groq(api_key=GROQ_API_KEY)

    plan_raw = _call_groq(
        client,
        topic_def["system"],
        PLAN_PROMPT.format(user_hint=topic_def["user_hint"], n_scenes=NUM_SCENES),
        json_mode=True,
    )
    plan = json.loads(plan_raw)
    plan = _normalize_plan(plan, topic_def["label"])

    print(f"   Plan : {plan.get('title', '?')} ({len(plan['scenes'])} scènes)")

    context = f"Sujet : {topic_def['label']}. Titre : {plan.get('title', '')}"
    final_scenes = []
    prev = plan.get("hook", "")

    for i, scene in enumerate(plan["scenes"]):
        narration = _expand(client, scene.get("idea", ""), context, prev)
        wc = _wc(narration)
        print(f"   Scène {i+1:>2}/{NUM_SCENES} · {wc} mots · {narration[:55]}...")
        final_scenes.append({
            "narration": narration,
            "visuals": scene.get("visuals", []),
            "image_prompt": scene.get("image_prompt", scene.get("idea", "")),
        })
        prev = narration

    total = sum(_wc(s["narration"]) for s in final_scenes)
    est_seconds = total * 0.41
    print(f"   📊 Total : {total} mots ≈ {est_seconds:.0f}s parlés (cible {TARGET_WORDS_MIN}-{TARGET_WORDS_MAX})")

    return {
        "title": plan.get("title", topic_def["label"]),
        "hook": plan.get("hook", ""),
        "scenes": final_scenes,
    }
