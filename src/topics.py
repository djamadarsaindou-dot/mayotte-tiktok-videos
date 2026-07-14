"""Thèmes des vidéos TikTok Mayotte.

5 thèmes en ROTATION (compteur persistant pour garantir la variété quotidienne) :
- decouverte_mayotte : lieux, faune, flore
- tradition_mahoraise : traditions et culture
- legende_mahoraise : légendes mahoraises
- fait_insolite : faits insolites
- actu_mayotte : actu réelles via RSS

Avec un cron 6h (4 vidéos/jour), la rotation passe par tous les thèmes sur
~30h, donc chaque thème revient environ tous les 1,2 jours.
"""
import random
from pathlib import Path

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
    # --- Thèmes MONDE (au-delà de Mayotte) — sujets à fort potentiel viral ---
    "espace": {
        "label": "Espace & Univers",
        "kind": "knowledge",
        "knowledge_theme": "espace",
    },
    "animaux": {
        "label": "Animaux incroyables",
        "kind": "knowledge",
        "knowledge_theme": "animaux",
    },
    "lieux_extremes": {
        "label": "Lieux extrêmes du monde",
        "kind": "knowledge",
        "knowledge_theme": "lieux_extremes",
    },
    "corps_humain": {
        "label": "Corps humain & cerveau",
        "kind": "knowledge",
        "knowledge_theme": "corps_humain",
    },
    "histoires_vraies": {
        "label": "Histoires vraies stupéfiantes",
        "kind": "knowledge",
        "knowledge_theme": "histoires_vraies",
    },
}

# Ordre de rotation : alterne MONDE (viral) et Mayotte (identité de la chaîne).
# Les sujets monde sont majoritaires (potentiel de percée), tout en gardant
# Mayotte régulièrement présent. Un thème ne revient jamais 2 fois de suite.
ROTATION_ORDER = [
    "espace",
    "decouverte_mayotte",
    "animaux",
    "histoires_vraies",
    "legende_mahoraise",
    "lieux_extremes",
    "corps_humain",
    "fait_insolite",
    "espace",
    "actu_mayotte",
    "animaux",
    "tradition_mahoraise",
    "histoires_vraies",
    "lieux_extremes",
    "corps_humain",
]

# Compteur persistant : output/rotation_counter.txt
_COUNTER_FILE = Path(__file__).resolve().parent.parent / "output" / "rotation_counter.txt"


def _read_counter() -> int:
    try:
        return int(_COUNTER_FILE.read_text(encoding="utf-8").strip())
    except Exception:
        return 0


def _write_counter(value: int) -> None:
    try:
        _COUNTER_FILE.parent.mkdir(parents=True, exist_ok=True)
        _COUNTER_FILE.write_text(str(value), encoding="utf-8")
    except Exception:
        pass


def next_topic() -> tuple[str, dict]:
    """Rotation déterministe : avance d'un cran à chaque appel.

    Garantit la variété entre les vidéos consécutives (pas 2 mêmes thèmes
    de suite). Le compteur est persisté sur disque.
    """
    counter = _read_counter()
    key = ROTATION_ORDER[counter % len(ROTATION_ORDER)]
    _write_counter(counter + 1)
    return key, TOPICS[key]


def random_topic() -> tuple[str, dict]:
    """Conservé pour compat — appelle next_topic() (rotation, pas aléatoire)."""
    return next_topic()
