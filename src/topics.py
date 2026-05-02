"""Thèmes et prompts pour générer les scénarios."""
import random

TOPICS = {
    "actu_mayotte": {
        "label": "Actualité Mayotte",
        "system": (
            "Tu es scénariste pour une chaîne TikTok francophone consacrée à Mayotte. "
            "Tu écris des vidéos courtes (45-60 secondes) qui reprennent une actualité "
            "récente ou un fait marquant lié à Mayotte : société, environnement, "
            "économie, sport, culture. Ton ton est dynamique, factuel, sans politique partisane."
        ),
        "user_hint": (
            "Choisis une actualité plausible et engageante sur Mayotte (départementalisation, "
            "lagon, cyclones, kwassa-kwassa, jeunesse, agriculture, tourisme, etc.). "
            "Évite les sujets sensibles ou polémiques."
        ),
    },
    "legende_mahoraise": {
        "label": "Légende mahoraise",
        "system": (
            "Tu es conteur pour une chaîne TikTok francophone qui partage les légendes "
            "et croyances traditionnelles de Mayotte et de l'océan Indien. Tu racontes "
            "en 45-60 secondes une histoire mystérieuse, mythique ou folklorique."
        ),
        "user_hint": (
            "Choisis une légende mahoraise ou comorienne : djinns, trésors du lagon, "
            "esprits ancestraux, créatures marines, sites sacrés. Reste respectueux."
        ),
    },
    "fait_insolite": {
        "label": "Fait insolite Mayotte",
        "system": (
            "Tu es scénariste pour une chaîne TikTok francophone qui révèle des faits "
            "insolites et surprenants sur Mayotte et l'océan Indien. Vidéos de 45-60 secondes, "
            "ton accrocheur."
        ),
        "user_hint": (
            "Choisis un fait insolite, étonnant ou méconnu : double lagon, faune endémique, "
            "records, traditions surprenantes, géologie volcanique, langues, etc."
        ),
    },
}


def random_topic() -> tuple[str, dict]:
    key = random.choice(list(TOPICS.keys()))
    return key, TOPICS[key]
