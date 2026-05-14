"""Génération d'images via Pollinations.ai (gratuit, sans inscription).

Stratégie qualité : on insiste pour avoir une image IA. On enchaîne flux → turbo,
avec backoff progressif et long, jusqu'à atteindre POLLINATIONS_MAX_RETRIES.
Seulement après on lève une exception (et stock_finder fait fallback).
"""
import time
import urllib.parse
from pathlib import Path

import requests

from src.config import POLLINATIONS_MAX_RETRIES, POLLINATIONS_MODEL, VIDEO_HEIGHT, VIDEO_WIDTH

POLLINATIONS_BASE = "https://image.pollinations.ai/prompt/"
TIMEOUT = 180


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
    output_path.parent.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    chain = _models_chain()
    max_retries = len(chain)

    for attempt in range(1, max_retries + 1):
        model = chain[attempt - 1]
        url = _build_url(prompt, model, seed)
        try:
            r = requests.get(url, timeout=TIMEOUT)
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
        except Exception as e:
            last_error = e
            wait = 4 + 3 * attempt  # 7, 10, 13, 16, 19, 22s
            print(f"  ⚠️  Essai {attempt}/{max_retries} ({model}) échoué : {str(e)[:80]}")
            time.sleep(wait)

    raise RuntimeError(
        f"Impossible de générer l'image après {max_retries} tentatives : {last_error}"
    )
