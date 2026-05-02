"""Génération d'images via Pollinations.ai (gratuit, sans inscription)."""
import time
import urllib.parse
from pathlib import Path

import requests

from src.config import VIDEO_HEIGHT, VIDEO_WIDTH

POLLINATIONS_BASE = "https://image.pollinations.ai/prompt/"
TIMEOUT = 90
MAX_RETRIES = 3


def generate_image(prompt: str, output_path: Path, seed: int | None = None) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    encoded = urllib.parse.quote(prompt)
    url = (
        f"{POLLINATIONS_BASE}{encoded}"
        f"?width={VIDEO_WIDTH}&height={VIDEO_HEIGHT}&nologo=true&model=flux"
    )
    if seed is not None:
        url += f"&seed={seed}"

    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(url, timeout=TIMEOUT)
            r.raise_for_status()
            output_path.write_bytes(r.content)
            return output_path
        except Exception as e:
            last_error = e
            print(f"  ⚠️  Tentative {attempt}/{MAX_RETRIES} échouée : {e}")
            time.sleep(2 * attempt)

    raise RuntimeError(f"Impossible de générer l'image après {MAX_RETRIES} tentatives : {last_error}")
