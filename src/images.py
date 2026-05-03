"""Génération d'images via Pollinations.ai (gratuit, sans inscription)."""
import time
import urllib.parse
from pathlib import Path

import requests

from src.config import POLLINATIONS_MODEL, VIDEO_HEIGHT, VIDEO_WIDTH

POLLINATIONS_BASE = "https://image.pollinations.ai/prompt/"
TIMEOUT = 120
MAX_RETRIES = 2  # En cas de rate-limit, on bascule vite sur le fallback stock


def _models_chain() -> list[str]:
    primary = POLLINATIONS_MODEL or "flux"
    return [primary, "turbo"]


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

    for attempt in range(1, MAX_RETRIES + 1):
        model = chain[(attempt - 1) % len(chain)]
        url = _build_url(prompt, model, seed)
        try:
            r = requests.get(url, timeout=TIMEOUT)
            if r.status_code == 429:
                wait = 5  # court : on bascule vite en fallback si ça persiste
                print(f"  ⏳ Rate limit ({model}), attente {wait}s (essai {attempt}/{MAX_RETRIES})")
                time.sleep(wait)
                continue
            r.raise_for_status()
            if len(r.content) < 1000:
                raise RuntimeError(f"Image trop petite ({len(r.content)} octets)")
            output_path.write_bytes(r.content)
            return output_path
        except Exception as e:
            last_error = e
            wait = 3
            print(f"  ⚠️  Essai {attempt}/{MAX_RETRIES} ({model}) échoué : {str(e)[:80]}")
            time.sleep(wait)

    raise RuntimeError(f"Impossible de générer l'image après {MAX_RETRIES} tentatives : {last_error}")
