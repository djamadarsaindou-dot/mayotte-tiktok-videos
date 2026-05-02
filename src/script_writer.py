"""Génération de scénarios ancrés sur des sujets vérifiés.

Pipeline en 2 passes :

1. ANCRAGE : on choisit un sujet précis
   - Pour les thèmes "knowledge" : un sujet aléatoire de la base de connaissances Mayotte
   - Pour "actu" : une actu réelle via RSS

2. PASSE A : le LLM propose un PLAN structuré (16 scènes) à partir du sujet ancré
3. PASSE B : pour chaque scène, le LLM rédige UNE phrase de 22-28 mots terminée par un point
"""
import json
import re

from src.config import (
    NUM_SCENES,
    TARGET_WORDS_MAX,
    TARGET_WORDS_MIN,
    VISUALS_PER_SCENE,
)
from src.llm import chat, chat_json, get_provider
from src.mayotte_knowledge import GLOBAL_CONTEXT_PROMPT, random_topic_for
from src.news_rss import fetch_recent_news, pick_news_topic


PLAN_PROMPT_KNOWLEDGE = """Tu vas écrire le plan d'un mini-reportage TikTok de 2min10 à 2min30 sur le sujet suivant à Mayotte.

SUJET (à narrer fidèlement, sans inventer) :
Titre : {title}
Faits vérifiés (utilise UNIQUEMENT ces faits, sans en ajouter d'autres) :
{facts}

À éviter : {avoid}

Renvoie UNIQUEMENT du JSON valide :
{{
  "title": "titre TikTok accrocheur (max 55 caractères) — peut être différent du titre source",
  "hook": "phrase d'accroche, 15-22 mots, intrigante",
  "scenes": [
    {{
      "idea": "1 phrase d'idée (12-18 mots) — utilise UN des faits ci-dessus",
      "fact_used": "le fait précis utilisé (copie-colle depuis la liste)",
      "visuals": ["3 mots-clés EN ANGLAIS visuel 1", "3 mots-clés visuel 2 (différent)", "3 mots-clés visuel 3 (différent)"],
      "image_prompt": "description en ANGLAIS d'une scène cinématique vertical 9:16 photoréaliste pour fallback IA"
    }}
  ]
}}

CONTRAINTES STRICTES :
- EXACTEMENT {n_scenes} scènes
- Construction narrative : intro accrocheuse → développement (au moins 4-5 angles concrets) → exemple ou témoignage → conclusion mémorable
- Chaque scène doit s'appuyer sur UN fait précis de la liste — pas d'invention
- Visuels SPÉCIFIQUES : ne te contente pas de "tropical island", décris ce qui doit être à l'écran
- Si la liste de faits a moins de {n_scenes} éléments, certains faits peuvent être développés sur 2-3 scènes différentes (sous des angles distincts)
"""


PLAN_PROMPT_NEWS = """Tu vas écrire le plan d'un mini-reportage TikTok de 2min10 à 2min30 sur cette actualité Mayotte récente.

ACTUALITÉ (à narrer fidèlement, sans inventer ni dramatiser) :
Titre : {news_title}
Source : {news_source}
Description : {news_description}

Renvoie UNIQUEMENT du JSON valide :
{{
  "title": "titre TikTok accrocheur (max 55 caractères)",
  "hook": "phrase d'accroche, 15-22 mots",
  "scenes": [
    {{
      "idea": "1 phrase d'idée pour cette scène (12-18 mots)",
      "visuals": ["3 mots-clés EN ANGLAIS visuel 1", "3 mots-clés visuel 2", "3 mots-clés visuel 3"],
      "image_prompt": "description en ANGLAIS d'une scène cinématique vertical 9:16 photoréaliste"
    }}
  ]
}}

CONTRAINTES :
- EXACTEMENT {n_scenes} scènes : intro contextualisant → développement de l'actualité → impact pour les Mahorais → ouverture
- Reste FACTUEL — ne dramatise pas, ne politise pas, ne prends pas parti
- Si tu manques d'infos, élargis avec le CONTEXTE GÉNÉRAL Mayotte (géographie, démographie, etc.)
- Visuels concrets, faciles à trouver en stock vidéo
"""


EXPAND_SYSTEM = (
    GLOBAL_CONTEXT_PROMPT
    + "\n\nTu rédiges les phrases de narration. Style oral fluide, dynamique, type Brut ou France TV Slash."
)

EXPAND_PROMPT = """Réécris cette idée en UNE phrase complète, fluide, à l'oral, en français.

Idée : {idea}
Contexte du reportage : {context}
{fact_block}
Phrase précédente (pour cohérence narrative) : {prev}

CONTRAINTES NON-NÉGOCIABLES :
- EXACTEMENT entre 22 et 28 mots
- UNE seule phrase
- DOIT se terminer par un point « . »
- Ton dynamique, narratif, oral, comme un reportage TF1/Brut
- Pas de répétition avec la phrase précédente
- Évite les énumérations à virgules en cascade
- Utilise « les Mahorais » (pas « les Mayottes »)
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


def _expand(idea: str, context: str, prev: str, fact: str | None = None) -> str:
    fact_block = f"Fait vérifié à narrer : {fact}\n" if fact else ""
    for attempt in range(3):
        prompt = EXPAND_PROMPT.format(
            idea=idea,
            context=context,
            fact_block=fact_block,
            prev=prev or "(début)",
        )
        sentence = _clean_sentence(chat(EXPAND_SYSTEM, prompt, temperature=0.7 + attempt * 0.1))
        wc = _wc(sentence)
        if 20 <= wc <= 30:
            return sentence
        if wc < 20:
            adjust = (
                f"La phrase fait {wc} mots, c'est trop court. Réécris-la pour qu'elle fasse "
                f"exactement entre 23 et 27 mots, en gardant le sens et le fait. Termine par un point. "
                f"Réponds avec UNIQUEMENT la phrase.\n\nPhrase : {sentence}"
            )
        else:
            adjust = (
                f"La phrase fait {wc} mots, c'est trop long. Réécris-la pour qu'elle fasse "
                f"exactement entre 23 et 27 mots, sans perdre le fait. Termine par un point. "
                f"Réponds avec UNIQUEMENT la phrase.\n\nPhrase : {sentence}"
            )
        sentence2 = _clean_sentence(chat(EXPAND_SYSTEM, adjust, temperature=0.5))
        if 20 <= _wc(sentence2) <= 30:
            return sentence2
    return sentence


def _normalize_plan(plan: dict, default_title: str) -> dict:
    scenes = plan.get("scenes", [])[:NUM_SCENES]
    while len(scenes) < NUM_SCENES:
        scenes.append({
            "idea": f"Conclusion sur {default_title}",
            "visuals": ["mayotte tropical sunset", "lagoon waves shore", "palm trees beach"],
            "image_prompt": "Mayotte tropical island at sunset, cinematic, vertical 9:16",
        })
    for s in scenes:
        visuals = s.get("visuals") or []
        if isinstance(visuals, str):
            visuals = [visuals]
        while len(visuals) < VISUALS_PER_SCENE:
            visuals.append(s.get("idea", default_title))
        s["visuals"] = visuals[:VISUALS_PER_SCENE]
    plan["scenes"] = scenes
    return plan


def _build_plan_for_knowledge(theme: str) -> tuple[dict, str, str]:
    """Renvoie (plan, context_for_expand, anchor_id)."""
    entry = random_topic_for(theme)
    facts_str = "\n".join(f"  • {f}" for f in entry["key_facts"])
    avoid_str = ", ".join(entry["avoid"]) if entry["avoid"] else "rien de spécifique"

    print(f"   🎯 Sujet ancré : {entry['title']}")

    user_prompt = PLAN_PROMPT_KNOWLEDGE.format(
        title=entry["title"],
        facts=facts_str,
        avoid=avoid_str,
        n_scenes=NUM_SCENES,
    )
    plan = chat_json(GLOBAL_CONTEXT_PROMPT, user_prompt, temperature=0.85)
    plan = _normalize_plan(plan, entry["title"])

    # Inject fact_used by-scene si LLM a oublié, on map proportionnellement
    if not all("fact_used" in s for s in plan["scenes"]):
        facts = entry["key_facts"]
        for i, s in enumerate(plan["scenes"]):
            s.setdefault("fact_used", facts[i % len(facts)])

    context = f"Sujet ancré : {entry['title']}. Titre TikTok : {plan.get('title', '')}"
    return plan, context, entry["title"]


def _build_plan_for_news() -> tuple[dict, str, str] | None:
    print("   📰 Recherche d'actualités Mayotte...")
    news = fetch_recent_news()
    chosen = pick_news_topic(news)
    if not chosen:
        print("   ⚠️  Aucune actu disponible, on bascule sur Découverte")
        return None
    print(f"   🎯 Actu choisie : [{chosen.source}] {chosen.title[:80]}")

    user_prompt = PLAN_PROMPT_NEWS.format(
        news_title=chosen.title,
        news_source=chosen.source,
        news_description=chosen.description or "(pas de description fournie)",
        n_scenes=NUM_SCENES,
    )
    plan = chat_json(GLOBAL_CONTEXT_PROMPT, user_prompt, temperature=0.7)
    plan = _normalize_plan(plan, chosen.title)
    context = f"Actualité Mayotte : {chosen.title}. Source : {chosen.source}"
    return plan, context, chosen.title


def generate_script(topic_def: dict) -> dict:
    print(f"   ⚙️  LLM provider : {get_provider()}")

    if topic_def.get("kind") == "rss":
        result = _build_plan_for_news()
        if result is None:
            # fallback sur Découverte
            plan, context, anchor = _build_plan_for_knowledge("decouverte_mayotte")
        else:
            plan, context, anchor = result
    else:
        plan, context, anchor = _build_plan_for_knowledge(topic_def["knowledge_theme"])

    print(f"   📋 Plan : {plan.get('title', '?')} ({len(plan['scenes'])} scènes)")

    final_scenes = []
    prev = plan.get("hook", "")

    for i, scene in enumerate(plan["scenes"]):
        narration = _expand(
            idea=scene.get("idea", ""),
            context=context,
            prev=prev,
            fact=scene.get("fact_used"),
        )
        wc = _wc(narration)
        print(f"   Scène {i+1:>2}/{NUM_SCENES} · {wc} mots · {narration[:55]}...")
        final_scenes.append({
            "narration": narration,
            "visuals": scene.get("visuals", []),
            "image_prompt": scene.get("image_prompt", scene.get("idea", "")),
            "fact_used": scene.get("fact_used"),
        })
        prev = narration

    total = sum(_wc(s["narration"]) for s in final_scenes)
    print(f"   📊 Total : {total} mots ≈ {total*0.41:.0f}s parlés (cible {TARGET_WORDS_MIN}-{TARGET_WORDS_MAX})")

    return {
        "title": plan.get("title", anchor),
        "hook": plan.get("hook", ""),
        "anchor": anchor,
        "scenes": final_scenes,
    }
