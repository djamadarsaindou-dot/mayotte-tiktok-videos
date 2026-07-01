"""Génération de scénarios ancrés sur des sujets vérifiés.

Pipeline en 2 passes :

1. ANCRAGE : on choisit un sujet précis
   - Pour les thèmes "knowledge" : un sujet aléatoire de la base de connaissances Mayotte
   - Pour "actu" : une actu réelle via RSS

2. PASSE A : le LLM propose un PLAN structuré (16 scènes) à partir du sujet ancré
3. PASSE B : pour chaque scène, le LLM rédige UNE phrase de 22-28 mots terminée par un point
"""
import json
import random
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


# Styles narratifs alternés aléatoirement pour éviter que toutes les vidéos
# aient la même structure (mystère / énumération / anecdote / comparaison).
# Le LLM reçoit les hints du style choisi et adapte le plan en conséquence.
NARRATIVE_STYLES = [
    {
        "name": "mystère",
        "intro_hint": (
            "Commence par une question intrigante ou un fait étrange qui "
            "crée une zone d'ombre — on doit avoir envie de connaître la suite."
        ),
        "construction": (
            "intro mystérieuse → indices accumulés → cliffhanger central "
            "« mais le plus fou, c'est… » → révélation finale qui éclaire tout"
        ),
        "closing_hint": (
            "Termine sur la révélation qui laisse pensif, puis demande au "
            "spectateur s'il connaissait + invite à s'abonner pour d'autres "
            "secrets de Mayotte."
        ),
    },
    {
        "name": "énumération",
        "intro_hint": (
            "Annonce d'emblée le nombre de choses à découvrir (« 5 choses "
            "incroyables sur… » ou « voici 3 secrets… »)."
        ),
        "construction": (
            "intro annonçant le nombre → énumération claire avec marqueurs "
            "« 1, 2, 3… » → un bonus inattendu en fin de liste → CTA"
        ),
        "closing_hint": (
            "Termine en disant « et le numéro 1 va te surprendre » ou un "
            "bonus surprise, puis invite à commenter son préféré."
        ),
    },
    {
        "name": "anecdote",
        "intro_hint": (
            "Commence comme si tu racontais une histoire vraie ou une "
            "rencontre personnelle (« Un Mahorais m'a raconté que… »)."
        ),
        "construction": (
            "scène d'ouverture immersive → développement narratif avec "
            "moments précis et sensations → conclusion qui tire une leçon"
        ),
        "closing_hint": (
            "Conclus par une réflexion personnelle ou un témoignage, puis "
            "demande au spectateur s'il vit la même chose."
        ),
    },
    {
        "name": "comparaison",
        "intro_hint": (
            "Oppose ce qu'on croit savoir à ce qu'on va découvrir "
            "(« Tu pensais X ? En vrai c'est très différent… »)."
        ),
        "construction": (
            "intro qui démonte une idée reçue → comparaisons multiples "
            "« avant / maintenant », « croyance / réalité » → vérité révélée"
        ),
        "closing_hint": (
            "Conclus en pointant ce qui change la perspective, puis invite "
            "à commenter si l'on avait soi-même cette idée reçue."
        ),
    },
]


# Hashtags spécifiques au thème (en plus du noyau mayotte/976/oceanindien)
HASHTAGS_BY_THEME = {
    "decouverte_mayotte": [
        "voyage", "tropical", "paradis", "lagon", "iledemayotte",
        "nature", "decouverte",
    ],
    "tradition_mahoraise": [
        "tradition", "culture", "shimaore", "patrimoine", "afrique",
        "culturefrancaise", "comores",
    ],
    "legende_mahoraise": [
        "legende", "mythologie", "mystere", "histoiresvraies", "spiritualite",
        "contes", "mystique",
    ],
    "fait_insolite": [
        "insolite", "saviezvous", "incroyable", "fact", "histoire",
        "anecdote",
    ],
    "actu_mayotte": [
        "actu", "info", "news", "actualite", "mayotte2026",
    ],
}

# Stratégie hashtags 2026 : EXACTEMENT 3-5 hashtags = 1-2 larges + 2-3 nichés.
# Les tags génériques « de portée » (#fyp/#pourtoi/#viral) sont ignorés voire
# pénalisés par l'algorithme TikTok → bannis du pool.
HASHTAGS_BROAD = ["mayotte", "outremer"]
HASHTAGS_NICHE_CORE = ["oceanindien", "culturemahoraise", "mahorais"]
BANNED_HASHTAGS = {
    "fyp", "fypage", "foryou", "foryoupage", "pourtoi", "pourtoipage",
    "viral", "virale", "tiktokfrance",
}

# Formules d'accroche interdites (hooks usés qui font scroller) — vérifiées
# dans le hook du plan ET dans la 1re phrase parlée (scène 1).
BANNED_HOOK_PHRASES = [
    "saviez-vous que", "saviez vous que", "et si je vous disais", "bienvenue",
]

# « Looks » visuels : UN look est tiré au sort par vidéo puis injecté dans
# TOUS les image_prompt — même éclairage/palette sur les 48 visuels
# (cohérence visuelle, la vidéo ne ressemble plus à un patchwork).
VISUAL_LOOKS = [
    "warm golden hour light, soft shadows, amber tones",
    "vivid tropical noon light, high clarity, saturated turquoise palette",
    "cool blue hour light, cinematic teal and orange grade",
    "soft overcast morning light, gentle pastel palette",
    "late afternoon sun, long shadows, warm cinematic film grade",
]

# Règles d'accroche communes aux 2 prompts de plan (knowledge + actu).
# La 1re phrase PARLÉE doit contenir « Mayotte » : l'ASR TikTok indexe la
# voix, c'est du SEO gratuit sur les 3 premières secondes.
_HOOK_RULES = """
CONTRAINTES STRICTES SUR L'ACCROCHE (hook + scène 1) :
- La 1re phrase du script (l'« idea » de la scène 1) = un FAIT CHOC SPÉCIFIQUE (chiffre précis, nom de lieu, ou superlatif vérifiable) ET contient obligatoirement le mot « Mayotte »
- Le champ "hook" suit les mêmes règles (fait choc spécifique + mot « Mayotte »)
- FORMULES INTERDITES, ni dans le hook ni dans les scènes : « Saviez-vous que », « Et si je vous disais », « Bienvenue »
- Choisis librement UNE de ces formules d'accroche (varie d'une vidéo à l'autre) :
  1. Affirmation contre-intuitive (qui contredit ce qu'on croit savoir)
  2. Question de VRAIE curiosité (pas une question rhétorique creuse)
  3. Preuve chiffrée d'abord (le chiffre le plus fort dès les premiers mots)
"""

# Règles de rétention communes : relances régulières + pic d'intérêt au
# milieu de la vidéo (~50% = point mort classique de la courbe de rétention).
_RETENTION_RULES = """
CONTRAINTES DE RÉTENTION :
- Toutes les 3-4 scènes, place un TURNING POINT : une info nouvelle ou un retournement qui relance l'attention (« mais en réalité… », « et c'est là que tout bascule »)
- Le fait LE PLUS insolite du sujet arrive vers la scène {mid_scene} (~50% de la vidéo) — PAS à la fin
- La scène 1 décrit l'image la plus spectaculaire du sujet : son image_prompt est le visuel le plus impressionnant de toute la vidéo
- LOOK VISUEL IMPOSÉ (cohérence des visuels) : chaque "image_prompt" se termine par « {look} » — même éclairage et même palette pour toute la vidéo
"""

# Description du champ visual_kind (routage IA / vrais clips vidéo stock).
_VISUAL_KIND_FIELD = (
    '"visual_kind": "ambiance" OU "specifique" — "ambiance" UNIQUEMENT si la '
    "scène s'illustre par un plan générique de nature (lagon, plage, océan, "
    "forêt, drone) sans personnage précis, sans lieu identifiable ni fait "
    'historique ; sinon "specifique". Vise 2 à 3 scènes "ambiance" par vidéo, '
    "jamais plus de 3."
)


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
  "hook_punch": "accroche ULTRA-courte de 3 à 5 mots, MAXIMUM 28 caractères, pour le texte d'accroche des 3 premières secondes (ex: 'Le secret du lagon', 'Personne ne sait ça')",
  "scenes": [
    {{
      "idea": "1 phrase d'idée (12-18 mots) — utilise UN des faits ci-dessus",
      "fact_used": "le fait précis utilisé (copie-colle depuis la liste)",
      "visual_kind": <{visual_kind_field}>,
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
- Style narratif imposé : {narrative_name}
  • Intro : {narrative_intro_hint}
  • Construction : {narrative_construction}
  • Conclusion (dernière scène) : {narrative_closing_hint}
- Chaque scène s'appuie sur UN fait précis de la liste — pas d'invention
""" + _HOOK_RULES + _RETENTION_RULES


PLAN_PROMPT_NEWS = """Tu vas écrire le plan d'un mini-reportage TikTok de 2min10 à 2min30 sur cette actualité Mayotte récente.

ACTUALITÉ (à narrer fidèlement, sans inventer ni dramatiser) :
Titre : {news_title}
Source : {news_source}
Description : {news_description}

Renvoie UNIQUEMENT du JSON valide :
{{
  "title": "titre TikTok accrocheur (max 55 caractères)",
  "hook": "phrase d'accroche, 15-22 mots",
  "hook_punch": "accroche ULTRA-courte de 3 à 5 mots, MAXIMUM 28 caractères, pour le texte d'accroche des 3 premières secondes",
  "scenes": [
    {{
      "idea": "1 phrase d'idée pour cette scène (12-18 mots)",
      "visual_kind": <{visual_kind_field}>,
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
""" + _HOOK_RULES + _RETENTION_RULES


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
- EXACTEMENT entre 24 et 29 mots
- UNE seule phrase
- DOIT se terminer par un point « . »
- Ton dynamique, narratif, oral, comme un reportage TF1/Brut
- Pas de répétition avec la phrase précédente
- Évite les énumérations à virgules en cascade
- Utilise « les Mahorais » (pas « les Mayottes »)
{extra_rules}- Réponds avec UNIQUEMENT la phrase, sans guillemets ni préfixe

Ta phrase :"""


# Règles supplémentaires pour la 1re phrase parlée de la vidéo (le hook) :
# « Mayotte » obligatoire (indexé par l'ASR TikTok) + pas de formule bannie.
HOOK_EXPAND_RULES = (
    "- C'est la TOUTE PREMIÈRE phrase de la vidéo : elle DOIT contenir le mot "
    "« Mayotte » et ouvrir sur le fait choc (chiffre, lieu ou superlatif) dès "
    "les premiers mots\n"
    "- INTERDIT de commencer par : « Saviez-vous que », « Et si je vous "
    "disais », « Bienvenue »\n"
)


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


def _hook_ok(sentence: str) -> bool:
    """Vrai si la phrase respecte les règles du hook parlé :
    contient « Mayotte » et aucune formule d'accroche bannie."""
    low = sentence.lower()
    return "mayotte" in low and not any(b in low for b in BANNED_HOOK_PHRASES)


def _expand(idea: str, context: str, prev: str, fact: str | None = None,
            is_hook: bool = False) -> str:
    fact_block = f"Fait vérifié à narrer : {fact}\n" if fact else ""
    extra_rules = HOOK_EXPAND_RULES if is_hook else ""
    sentence = ""
    for attempt in range(3):
        prompt = EXPAND_PROMPT.format(
            idea=idea,
            context=context,
            fact_block=fact_block,
            prev=prev or "(début)",
            extra_rules=extra_rules,
        )
        sentence = _clean_sentence(chat(EXPAND_SYSTEM, prompt, temperature=0.7 + attempt * 0.1))
        wc = _wc(sentence)
        if 22 <= wc <= 31 and (not is_hook or _hook_ok(sentence)):
            return sentence
        if is_hook and not _hook_ok(sentence):
            # Hook non conforme (« Mayotte » absent ou formule bannie) :
            # on retente avec une température différente.
            continue
        if wc < 22:
            adjust = (
                f"La phrase fait {wc} mots, c'est trop court. Réécris-la pour qu'elle fasse "
                f"exactement entre 25 et 28 mots, en gardant le sens et le fait. Termine par un point. "
                f"Réponds avec UNIQUEMENT la phrase.\n\nPhrase : {sentence}"
            )
        else:
            adjust = (
                f"La phrase fait {wc} mots, c'est trop long. Réécris-la pour qu'elle fasse "
                f"exactement entre 25 et 28 mots, sans perdre le fait. Termine par un point. "
                f"Réponds avec UNIQUEMENT la phrase.\n\nPhrase : {sentence}"
            )
        sentence2 = _clean_sentence(chat(EXPAND_SYSTEM, adjust, temperature=0.5))
        if 22 <= _wc(sentence2) <= 31 and (not is_hook or _hook_ok(sentence2)):
            return sentence2
    # Dernier filet pour le hook : on injecte « Mayotte » si toujours absent
    # (l'ASR TikTok indexe la voix — le mot doit être prononcé en 1er).
    if is_hook and sentence and "mayotte" not in sentence.lower():
        print("   ⚠️  Hook sans « Mayotte » après 3 essais → injection manuelle")
        sentence = _ensure_period("À Mayotte, " + sentence[0].lower() + sentence[1:])
    return sentence


# Plafond de scènes « ambiance » : 3 scènes × 4 visuels = 12 clips stock max
# par vidéo (le budget recommandé est 8-12 vrais clips vidéo).
AMBIANCE_MAX_SCENES = 3


def _fallback_hook_punch(hook: str) -> str:
    """Fabrique le texte d'accroche court à partir du hook : les 3-5 premiers
    mots nettoyés, 28 caractères max. Utilisé quand le LLM renvoie un
    hook_punch vide (bug : l'accroche des 3 premières secondes disparaissait)."""
    words = re.findall(r"[\w'’À-ÿ-]+", hook or "")[:5]
    while len(words) > 3 and len(" ".join(words)) > 28:
        words.pop()
    return " ".join(words)[:28].strip()


def _normalize_plan(plan: dict, default_title: str, look: str = "") -> dict:
    scenes = plan.get("scenes", [])[:NUM_SCENES]
    while len(scenes) < NUM_SCENES:
        scenes.append({
            "idea": f"Conclusion sur {default_title}",
            "visual_kind": "ambiance",
            "visuals": ["mayotte tropical sunset", "lagoon waves shore", "palm trees beach"],
            "image_prompt": "Mayotte tropical island at sunset, cinematic, vertical 9:16",
        })
    ambiance_count = 0
    for s in scenes:
        visuals = s.get("visuals") or []
        if isinstance(visuals, str):
            visuals = [visuals]
        while len(visuals) < VISUALS_PER_SCENE:
            visuals.append(s.get("idea", default_title))
        s["visuals"] = visuals[:VISUALS_PER_SCENE]

        # visual_kind : "ambiance" (plan générique → vrai clip vidéo stock)
        # ou "specifique" (image IA). Défaut si absent/invalide : specifique.
        kind = str(s.get("visual_kind") or "").strip().lower()
        if kind not in ("ambiance", "specifique"):
            kind = "specifique"
        if kind == "ambiance":
            ambiance_count += 1
            if ambiance_count > AMBIANCE_MAX_SCENES:
                kind = "specifique"  # garde le budget ~8-12 clips stock
        s["visual_kind"] = kind

        # Cohérence visuelle : chaque image_prompt hérite du même look
        # (éclairage/palette identiques sur toute la vidéo).
        prompt = str(s.get("image_prompt") or s.get("idea") or default_title).strip()
        if look and look.lower() not in prompt.lower():
            prompt = f"{prompt}, {look}"
        s["image_prompt"] = prompt

    plan["scenes"] = scenes

    # hook_punch : fallback sur les premiers mots du hook si le LLM renvoie
    # une chaîne vide (avant : chaîne vide → pas de texte d'accroche à l'écran).
    punch = (plan.get("hook_punch") or "").strip()
    if not punch:
        punch = _fallback_hook_punch(plan.get("hook") or default_title)
    plan["hook_punch"] = punch[:28].strip()
    return plan


def _build_plan_for_knowledge(theme: str, look: str = "") -> tuple[dict, str, str]:
    """Renvoie (plan, context_for_expand, anchor_id)."""
    entry = random_topic_for(theme)
    facts_str = "\n".join(f"  • {f}" for f in entry["key_facts"])
    visual_hints_str = "\n".join(f"  • {h}" for h in entry.get("visual_hints", []))
    avoid_str = ", ".join(entry["avoid"]) if entry["avoid"] else "rien de spécifique"

    # Tire au sort un style narratif pour varier la structure d'une vidéo à
    # l'autre (mystère / énumération / anecdote / comparaison).
    style = random.choice(NARRATIVE_STYLES)

    print(f"   🎯 Sujet ancré : {entry['title']}")
    print(f"   🎭 Style narratif : {style['name']}")

    user_prompt = PLAN_PROMPT_KNOWLEDGE.format(
        title=entry["title"],
        facts=facts_str,
        visual_hints=visual_hints_str or "  (aucun, utilise le contexte général Mayotte)",
        avoid=avoid_str,
        n_scenes=NUM_SCENES,
        n_visuals=VISUALS_PER_SCENE,
        narrative_name=style["name"],
        narrative_intro_hint=style["intro_hint"],
        narrative_construction=style["construction"],
        narrative_closing_hint=style["closing_hint"],
        visual_kind_field=_VISUAL_KIND_FIELD,
        mid_scene=NUM_SCENES // 2,
        look=look,
    )
    plan = chat_json(GLOBAL_CONTEXT_PROMPT, user_prompt, temperature=0.85)
    plan = _normalize_plan(plan, entry["title"], look=look)

    # Injecte fact_used scène par scène si le LLM a oublié : mapping ORDONNÉ
    # (chaque fait couvre un bloc de scènes consécutives, dans l'ordre de la
    # liste) au lieu du modulo qui recyclait les faits dans le désordre.
    if not all("fact_used" in s for s in plan["scenes"]):
        facts = entry["key_facts"]
        n = len(plan["scenes"]) or 1
        for i, s in enumerate(plan["scenes"]):
            s.setdefault("fact_used", facts[min(i * len(facts) // n, len(facts) - 1)])

    context = f"Sujet ancré : {entry['title']}. Titre TikTok : {plan.get('title', '')}"
    return plan, context, entry["title"]


def _build_plan_for_news(look: str = "") -> tuple[dict, str, str] | None:
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
        visual_kind_field=_VISUAL_KIND_FIELD,
        mid_scene=NUM_SCENES // 2,
        look=look,
    )
    plan = chat_json(GLOBAL_CONTEXT_PROMPT, user_prompt, temperature=0.7)
    plan = _normalize_plan(plan, chosen.title, look=look)
    context = f"Actualité Mayotte : {chosen.title}. Source : {chosen.source}"
    return plan, context, chosen.title


CAPTION_PROMPT = """Tu écris la LÉGENDE TikTok (optimisée SEO) pour cette vidéo sur Mayotte.

Titre de la vidéo : {title}
Sujet : {anchor}
Accroche : {hook}

Renvoie UNIQUEMENT du JSON :
{{
  "caption": "description TikTok de 150 caractères max. Le MOT-CLÉ LONG-TAIL du sujet (ex. « lagon de Mayotte », « légende mahoraise du lac Dziani ») DOIT apparaître dans les 100 PREMIERS caractères. 1-2 emojis bien placés. Termine par une mini-question qui invite à commenter",
  "hashtags": ["EXACTEMENT 3 à 5 hashtags SANS le # : 1-2 larges (mayotte, outremer) + 2-3 nichés collés au sujet précis (ex. oceanindien, culturemahoraise, lagondemayotte)"]
}}

CONTRAINTES :
- Le mot-clé long-tail décrit le sujet PRÉCIS de la vidéo (pas juste « Mayotte »)
- INTERDIT : fyp, pourtoi, foryou, viral et tout hashtag générique « de portée »
- Pas de hashtags trompeurs
- Français
"""


def generate_caption(title: str, anchor: str, hook: str, theme: str = "") -> dict:
    """Génère la légende + hashtags TikTok. Renvoie {'caption', 'hashtags', 'text'}.

    Stratégie SEO TikTok 2026 :
    - Le mot-clé long-tail du sujet dans les 100 premiers caractères (imposé au LLM)
    - EXACTEMENT 3-5 hashtags : 1-2 larges (mayotte, outremer) + 2-3 nichés
      (oceanindien, culturemahoraise, thème du jour…)
    - Aucun hashtag générique de portée (#fyp/#pourtoi/#viral) — bannis
    """
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
        tags = []

    # Le LLM déborde parfois les 150 caractères demandés : on coupe proprement
    # à la fin de la dernière phrase complète sous 220 caractères (le mot-clé
    # SEO des 100 premiers caractères est préservé).
    if len(caption) > 220:
        cut = caption[:220]
        end = max(cut.rfind("."), cut.rfind("!"), cut.rfind("?"), cut.rfind("…"))
        caption = (cut[:end + 1] if end > 60 else cut).strip()

    # Nettoie les hashtags LLM : sans #, sans espace, minuscules, sans bannis
    clean_tags: list[str] = []
    for t in tags:
        t = re.sub(r"[^\w]", "", str(t)).lower()
        if t and t not in clean_tags and t not in BANNED_HASHTAGS:
            clean_tags.append(t)

    # 1-2 hashtags LARGES en tête (mayotte toujours, outremer ensuite)
    broad = [t for t in HASHTAGS_BROAD if t in clean_tags]
    for t in HASHTAGS_BROAD:
        if t not in broad:
            broad.append(t)
    broad = broad[:2]

    # 2-3 hashtags NICHÉS : ceux du LLM d'abord (collés au sujet précis),
    # puis la banque thématique (thème du jour), puis le noyau niche.
    niche = [t for t in clean_tags if t not in broad]
    theme_pool = [t for t in HASHTAGS_BY_THEME.get(theme, []) if t not in BANNED_HASHTAGS]
    if theme_pool:
        for t in random.sample(theme_pool, min(2, len(theme_pool))):
            if t not in niche:
                niche.append(t)
    for t in HASHTAGS_NICHE_CORE:
        if t not in niche and t not in broad:
            niche.append(t)
    niche = niche[:3]

    # Total : exactement 3-5 hashtags (1-2 larges + 2-3 nichés)
    final = (broad + niche)[:5]

    # Contrôle SEO doux : le mot-clé du sujet doit apparaître dans les 100
    # premiers caractères de la description (l'algorithme indexe ce segment).
    head = caption[:100].lower()
    anchor_tokens = re.findall(r"\w{4,}", anchor.lower())
    if anchor_tokens and not any(w in head for w in anchor_tokens) and "mayotte" not in head:
        print("   ⚠️  SEO : mot-clé long-tail absent des 100 premiers caractères de la légende")

    hashtag_line = " ".join(f"#{t}" for t in final)
    full_text = f"{caption}\n\n{hashtag_line}"
    return {"caption": caption, "hashtags": final, "text": full_text}


def generate_script(topic_def: dict) -> dict:
    print(f"   ⚙️  LLM provider : {get_provider()}")

    # Cohérence visuelle : UN look (éclairage/palette) tiré au sort pour TOUTE
    # la vidéo — chaque image_prompt en hérite (48 visuels homogènes).
    look = random.choice(VISUAL_LOOKS)
    print(f"   🎨 Look visuel : {look}")

    if topic_def.get("kind") == "rss":
        result = _build_plan_for_news(look=look)
        if result is None:
            # fallback sur Découverte
            plan, context, anchor = _build_plan_for_knowledge("decouverte_mayotte", look=look)
        else:
            plan, context, anchor = result
    else:
        plan, context, anchor = _build_plan_for_knowledge(topic_def["knowledge_theme"], look=look)

    print(f"   📋 Plan : {plan.get('title', '?')} ({len(plan['scenes'])} scènes)")

    final_scenes = []
    prev = plan.get("hook", "")

    for i, scene in enumerate(plan["scenes"]):
        narration = _expand(
            idea=scene.get("idea", ""),
            context=context,
            prev=prev,
            fact=scene.get("fact_used"),
            is_hook=(i == 0),  # scène 1 = hook parlé : « Mayotte » obligatoire
        )
        wc = _wc(narration)
        print(f"   Scène {i+1:>2}/{NUM_SCENES} · {wc} mots · {narration[:55]}...")
        final_scenes.append({
            "narration": narration,
            "visuals": scene.get("visuals", []),
            "image_prompt": scene.get("image_prompt", scene.get("idea", "")),
            "fact_used": scene.get("fact_used"),
            # Routage smart mix : "ambiance" → vrai clip stock, sinon IA
            "visual_kind": scene.get("visual_kind", "specifique"),
        })
        prev = narration

    total = sum(_wc(s["narration"]) for s in final_scenes)
    print(f"   📊 Total : {total} mots ≈ {total*0.41:.0f}s parlés (cible {TARGET_WORDS_MIN}-{TARGET_WORDS_MAX})")

    title = plan.get("title", anchor)
    hook = plan.get("hook", "")

    # Légende TikTok (description + hashtags) prête à copier-coller.
    # On passe le thème pour enrichir les hashtags avec la banque thématique.
    theme = topic_def.get("knowledge_theme") or topic_def.get("kind", "")
    print("   📱 Génération de la légende TikTok...")
    caption = generate_caption(title, anchor, hook, theme=theme)

    return {
        "title": title,
        "hook": hook,
        # _normalize_plan garantit un hook_punch non vide (fallback = 3-5
        # premiers mots du hook), plus jamais de chaîne vide ici.
        "hook_punch": (plan.get("hook_punch") or "").strip(),
        "anchor": anchor,
        "look": look,
        "scenes": final_scenes,
        "caption": caption,
    }
