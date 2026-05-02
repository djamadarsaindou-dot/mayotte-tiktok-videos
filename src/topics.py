"""Thèmes des vidéos TikTok Mayotte.

4 thèmes :
- decouverte_mayotte : lieux, faune, flore (sujets pris dans la base de connaissances)
- tradition_mahoraise : traditions et culture (base de connaissances)
- legende_mahoraise : légendes mahoraises (base de connaissances)
- fait_insolite : faits insolites Mayotte (base de connaissances)
- actu_mayotte : actu réelles via RSS (Mayotte la 1ère, etc.)
"""
import random

TOPICS = {
    "decouverte_mayotte": {
        "label": "Découverte Mayotte",
        "kind": "knowledge",
        "knowledge_theme": "decouverte_mayotte",
    },
    "tradition_mahoraise": {
        "label": "Tradition mahoraise",
        "kind": "knowledge",
        "knowledge_theme": "tradition_mahoraise",
    },
    "legende_mahoraise": {
        "label": "Légende mahoraise",
        "kind": "knowledge",
        "knowledge_theme": "legende_mahoraise",
    },
    "fait_insolite": {
        "label": "Fait insolite Mayotte",
        "kind": "knowledge",
        "knowledge_theme": "fait_insolite",
    },
    "actu_mayotte": {
        "label": "Actu Mayotte",
        "kind": "rss",
    },
}


def random_topic() -> tuple[str, dict]:
    key = random.choice(list(TOPICS.keys()))
    return key, TOPICS[key]
