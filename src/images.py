"""Génération d'images via Pollinations.ai.

Stratégie qualité : on insiste pour avoir une image IA. On enchaîne flux → turbo,
avec backoff progressif, jusqu'à atteindre POLLINATIONS_MAX_RETRIES. Seulement
après on lève une exception (et stock_finder fait fallback).

CIRCUIT BREAKER : si Pollinations renvoie une erreur DÉFINITIVE (402 Payment
Required, 401, 403), on sait que le service est payant/bloqué — inutile de
réessayer pour les autres images. Un flag global coupe Pollinations pour tout
le reste du process : les images suivantes tombent instantanément en fallback
stock. Évite de perdre des heures en retries inutiles.
"""
import threading
import time
import urllib.parse
from pathlib import Path

import requests

from src.config import (
    POLLINATIONS_ENABLED,
    POLLINATIONS_MAX_RETRIES,
    POLLINATIONS_MODEL,
    VIDEO_HEIGHT,
    VIDEO_WIDTH,
)

POLLINATIONS_BASE = "https://image.pollinations.ai/prompt/"
TIMEOUT = 180

# Codes HTTP « définitifs » : réessayer ne sert à rien (service payant/bloqué).
FATAL_STATUS = (401, 402, 403)

# Circuit breaker partagé entre threads. Une fois levé, generate_image lève
# immédiatement sans tenter de requête réseau.
_breaker = threading.Event()
_breaker_reason = ""


class PollinationsUnavailable(RuntimeError):
    """Pollinations est indisponible de façon définitive (paiement requis, etc.).

    Distincte d'un échec transitoire : le caller ne doit PAS réessayer.
    """


def is_available() -> bool:
    """Vrai si Pollinations peut encore être tenté ce run."""
    return POLLINATIONS_ENABLED and not _breaker.is_set()


def _trip_breaker(reason: str) -> None:
    global _breaker_reason
    if not _breaker.is_set():
        _breaker_reason = reason
        _breaker.set()
        print(f"  🚫 Pollinations désactivé pour ce run : {reason}")
        print(f"     → toutes les images suivantes passent direct en stock.")


def _models_chain() -> list[str]:
    """Alterne flux (qualité) et turbo (rapide, débloque parfois).
    On commence par flux, et on insère du turbo pour casser un éventuel blocage."""
    primary = POLLINATIONS_MODEL or "flux"
    chain = [primary, primary, "turbo", primary, primary, "turbo", primary, primary]
    return chain[: max(POLLINATIONS_MAX_RETRIES, 2)]


def _build_url(prompt: str, model: str, seed: int | None) -> str:
    encoded = urllib.parse.quote(prompt)
    url = (
        f"{POLLINATIONS_BASE}{encoded}"
        f"?width={VIDEO_WIDTH}&height={VIDEO_HEIGHT}&nologo=true&enhance=false&model={model}"
    )
    if seed is not None:
        url += f"&seed={seed}"
    return url


def generate_image(prompt: str, output_path: Path, seed: int | None = None) -> Path:
    # Court-circuit : Pollinations désactivé (config) ou breaker déjà levé.
    if not POLLINATIONS_ENABLED:
        raise PollinationsUnavailable("Pollinations désactivé (POLLINATIONS_ENABLED=false)")
    if _breaker.is_set():
        raise PollinationsUnavailable(f"Pollinations indisponible ({_breaker_reason})")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    chain = _models_chain()
    max_retries = len(chain)

    for attempt in range(1, max_retries + 1):
        # Un autre thread a pu lever le breaker entre-temps.
        if _breaker.is_set():
            raise PollinationsUnavailable(f"Pollinations indisponible ({_breaker_reason})")

        model = chain[attempt - 1]
        url = _build_url(prompt, model, seed)
        try:
            r = requests.get(url, timeout=TIMEOUT)

            # Erreur DÉFINITIVE → on coupe Pollinations pour tout le run.
            if r.status_code in FATAL_STATUS:
                _trip_breaker(f"HTTP {r.status_code} (service payant ou accès refusé)")
                raise PollinationsUnavailable(f"Pollinations HTTP {r.status_code}")

            if r.status_code == 429:
                wait = 8 + 5 * attempt  # 13, 18, 23, 28, 33, 38, 43, 48s
                print(f"  ⏳ Rate limit ({model}), attente {wait}s "
                      f"(essai {attempt}/{max_retries})")
                time.sleep(wait)
                continue

            r.raise_for_status()
            if len(r.content) < 1000:
                raise RuntimeError(f"Image trop petite ({len(r.content)} octets)")
            output_path.write_bytes(r.content)
            return output_path

        except PollinationsUnavailable:
            # Erreur définitive : on propage tout de suite, AUCUN retry.
            raise
        except Exception as e:
            last_error = e
            wait = 4 + 3 * attempt  # 7, 10, 13, 16, 19, 22s
            print(f"  ⚠️  Essai {attempt}/{max_retries} ({model}) échoué : {str(e)[:80]}")
            time.sleep(wait)

    raise RuntimeError(
        f"Impossible de générer l'image après {max_retries} tentatives : {last_error}"
    )
