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

INDICES VISUELS POUR LE SUJET (à utiliser comme inspiration pour les image_prompt) :
{visual_hints}

À éviter : {avoid}

Renvoie UNIQUEMENT du JSON valide :
{{
  "title": "titre TikTok accrocheur (max 55 caractères) — peut être différent du titre source",
  "hook": "phrase d'accroche, 15-22 mots, intrigante",
  "hook_punch": "accroche ULTRA-courte de 3 à 6 mots pour le texte géant des 3 premières secondes (ex: 'Le secret du lagon', 'Personne ne sait ça', 'Mayotte va te surprendre')",
  "scenes": [
    {{
      "idea": "1 phrase d'idée (12-18 mots) — utilise UN des faits ci-dessus",
      "fact_used": "le fait précis utilisé (copie-colle depuis la liste)",
      "visuals": [<EXACTEMENT {n_visuals} PHRASES EN ANGLAIS, chacune décrivant une SCÈNE PHYSIQUE CONCRÈTE visible à l'écran, angles différents (large/moyen/gros-plan/détail)>],
      "image_prompt": "description en ANGLAIS riche et détaillée d'une scène cinématique vertical 9:16 photoréaliste de Mayotte"
    }}
  ]
}}

EXEMPLES de "visuals" CORRECTS (concrets, angles variés) :
  ✅ "aerial drone shot turquoise tropical lagoon coral reef sunny day"
  ✅ "fishermen pulling traditional net on shallow water at dawn"
  ✅ "close-up colorful tropical fish swimming around coral"
  ✅ "elderly woman teaching young girl to weave palm leaves"

CONTRAINTES STRICTES POUR LES VISUELS :
- INTERDIT : abstractions ("ancient tradition", "sisterhood", "cultural heritage", "moment of joy"). Trop vague pour générer une image.
- OBLIGATOIRE : phrases visuelles décrivant CE QUI EST À L'ÉCRAN. Format « action + sujet + lieu/objet ».
- EXACTEMENT {n_visuals} visuels par scène, TOUS DIFFÉRENTS, angles variés (aérien, moyen, gros plan, ambiance, geste, objet…)
- Chaque visual de 6 à 12 mots, suffisamment précis pour générer une image IA cohérente

CONTRAINTES STRICTES NARRATIVES :
- EXACTEMENT {n_scenes} scènes
- Construction : intro accrocheuse → développement (4-5 angles concrets) → exemple ou témoignage → conclusion
- LA DERNIÈRE SCÈNE doit être une QUESTION engageante au spectateur + invitation à commenter/s'abonner (ex: "Et toi, tu connaissais cette légende ? Dis-le en commentaire et abonne-toi pour découvrir Mayotte !")
- Au milieu du récit (scène 6 ou 7), glisse un mini-cliffhanger ("mais le plus fou, c'est…", "et ce que personne ne sait…")
- Chaque scène s'appuie sur UN fait précis de la liste — pas d'invention
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
  "hook_punch": "accroche ULTRA-courte de 3 à 6 mots pour le texte géant des 3 premières secondes",
  "scenes": [
    {{
      "idea": "1 phrase d'idée pour cette scène (12-18 mots)",
      "visuals": [<EXACTEMENT {n_visuals} PHRASES EN ANGLAIS, scènes physiques concrètes, angles variés>],
      "image_prompt": "description en ANGLAIS d'une scène cinématique vertical 9:16 photoréaliste"
    }}
  ]
}}

CONTRAINTES :
- EXACTEMENT {n_scenes} scènes : intro contextualisant → développement de l'actualité → impact pour les Mahorais → ouverture
- LA DERNIÈRE SCÈNE doit être une QUESTION au spectateur + invitation à commenter/s'abonner
- Reste FACTUEL — ne dramatise pas, ne politise pas, ne prends pas parti
- Si tu manques d'infos, élargis avec le CONTEXTE GÉNÉRAL Mayotte (géographie, démographie, etc.)
- Visuels concrets décrivant CE QUI EST À L'ÉCRAN (action + sujet + lieu), 6-12 mots, tous différents.
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
- EXACTEMENT entre 19 et 24 mots
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
        if 17 <= wc <= 26:
            return sentence
        if wc < 17:
            adjust = (
                f"La phrase fait {wc} mots, c'est trop court. Réécris-la pour qu'elle fasse "
                f"exactement entre 20 et 23 mots, en gardant le sens et le fait. Termine par un point. "
                f"Réponds avec UNIQUEMENT la phrase.\n\nPhrase : {sentence}"
            )
        else:
            adjust = (
                f"La phrase fait {wc} mots, c'est trop long. Réécris-la pour qu'elle fasse "
                f"exactement entre 20 et 23 mots, sans perdre le fait. Termine par un point. "
                f"Réponds avec UNIQUEMENT la phrase.\n\nPhrase : {sentence}"
            )
        sentence2 = _clean_sentence(chat(EXPAND_SYSTEM, adjust, temperature=0.5))
        if 17 <= _wc(sentence2) <= 26:
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
    visual_hints_str = "\n".join(f"  • {h}" for h in entry.get("visual_hints", []))
    avoid_str = ", ".join(entry["avoid"]) if entry["avoid"] else "rien de spécifique"

    print(f"   🎯 Sujet ancré : {entry['title']}")

    user_prompt = PLAN_PROMPT_KNOWLEDGE.format(
        title=entry["title"],
        facts=facts_str,
        visual_hints=visual_hints_str or "  (aucun, utilise le contexte général Mayotte)",
        avoid=avoid_str,
        n_scenes=NUM_SCENES,
        n_visuals=VISUALS_PER_SCENE,
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
        n_visuals=VISUALS_PER_SCENE,
    )
    plan = chat_json(GLOBAL_CONTEXT_PROMPT, user_prompt, temperature=0.7)
    plan = _normalize_plan(plan, chosen.title)
    context = f"Actualité Mayotte : {chosen.title}. Source : {chosen.source}"
    return plan, context, chosen.title


CAPTION_PROMPT = """Tu écris la LÉGENDE TikTok pour cette vidéo sur Mayotte.

Titre de la vidéo : {title}
Sujet : {anchor}
Accroche : {hook}

Renvoie UNIQUEMENT du JSON :
{{
  "caption": "1 à 2 phrases engageantes pour la description TikTok, avec 2-3 emojis bien placés, qui donne envie de regarder ET de commenter (pose une mini-question à la fin)",
  "hashtags": ["liste de 10 à 14 hashtags SANS le # — mélange hashtags larges (mayotte, oceanindien, dom976) et hashtags de niche liés au sujet"]
}}

CONTRAINTES :
- Le caption fait 150 caractères max
- Hashtags pertinents : toujours inclure mayotte, 976, oceanindien ; ajoute des hashtags liés au thème précis
- Pas de hashtags interdits ou trompeurs
- Français
"""


def generate_caption(title: str, anchor: str, hook: str) -> dict:
    """Génère la légende + hashtags TikTok. Renvoie {'caption', 'hashtags', 'text'}."""
    try:
        data = chat_json(
            "Tu es expert en croissance TikTok francophone.",
            CAPTION_PROMPT.format(title=title, anchor=anchor, hook=hook),
            temperature=0.8,
        )
        caption = (data.get("caption") or title).strip()
        tags = data.get("hashtags") or []
    except Exception as e:
        print(f"   ⚠️  Génération légende échouée ({str(e)[:60]}), fallback simple")
        caption = title
        tags = ["mayotte", "976", "oceanindien", "dom", "tiktokvoyage"]

    # Nettoie les hashtags : sans #, sans espace, minuscules
    clean_tags = []
    for t in tags:
        t = re.sub(r"[^\w]", "", str(t)).lower()
        if t and t not in clean_tags:
            clean_tags.append(t)
    for must in ("mayotte", "976", "oceanindien"):
        if must not in clean_tags:
            clean_tags.insert(0, must)

    hashtag_line = " ".join(f"#{t}" for t in clean_tags[:14])
    full_text = f"{caption}\n\n{hashtag_line}"
    return {"caption": caption, "hashtags": clean_tags[:14], "text": full_text}


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

    title = plan.get("title", anchor)
    hook = plan.get("hook", "")

    # Légende TikTok (description + hashtags) prête à copier-coller
    print("   📱 Génération de la légende TikTok...")
    caption = generate_caption(title, anchor, hook)

    return {
        "title": title,
        "hook": hook,
        "hook_punch": (plan.get("hook_punch") or "").strip(),
        "anchor": anchor,
        "scenes": final_scenes,
        "caption": caption,
    }
