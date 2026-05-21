"""Génération d'images IA via Cloudflare Workers AI (modèle FLUX-1-schnell).

Remplace Pollinations.ai, devenu payant en mai 2026.

Free tier Cloudflare : 10 000 neurons/jour, renouvelés quotidiennement, sans
carte bancaire. Une image FLUX-schnell coûte ~70-80 neurons → ~130 images/jour
possibles (le cron en consomme ~48/jour, large marge).

CIRCUIT BREAKER : si Cloudflare renvoie une erreur définitive (401/403 token
invalide, 429 quota épuisé), un flag coupe Cloudflare pour le reste du run —
les images suivantes tombent direct en fallback stock, sans retry inutile.

Setup :
1. Compte gratuit sur https://dash.cloudflare.com/sign-up (sans CB)
2. Account ID : visible dans Workers & Pages (barre de droite)
3. API Token : https://dash.cloudflare.com/profile/api-tokens
   → Create Token → template « Workers AI » → Create
4. Dans .env :
   CLOUDFLARE_ACCOUNT_ID=...
   CLOUDFLARE_API_TOKEN=...

Note : FLUX-1-schnell génère des images carrées (pas de paramètre de
dimension). Le montage FFmpeg recadre ensuite en 9:16 — d'où le « centered
subject » ajouté au prompt côté stock_finder.
"""
from __future__ import annotations

import base64
import threading
import time
from pathlib import Path

import requests

from src.config import CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN

MODEL = "@cf/black-forest-labs/flux-1-schnell"
TIMEOUT = 120
MAX_RETRIES = 3
STEPS = 4  # FLUX-schnell : 4 steps suffisent (max 8), bon compromis qualité/coût

# Circuit breaker partagé entre threads.
_breaker = threading.Event()
_breaker_reason = ""


class CloudflareUnavailable(RuntimeError):
    """Cloudflare AI indisponible de façon définitive (quota, token invalide).

    Le caller ne doit PAS réessayer : il doit basculer en fallback stock.
    """


def is_configured() -> bool:
    """Vrai si les identifiants Cloudflare sont présents dans .env."""
    return bool(CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN)


def is_available() -> bool:
    """Vrai si Cloudflare peut encore être tenté ce run."""
    return is_configured() and not _breaker.is_set()


def _trip_breaker(reason: str) -> None:
    global _breaker_reason
    if not _breaker.is_set():
        _breaker_reason = reason
        _breaker.set()
        print(f"  🚫 Cloudflare AI désactivé pour ce run : {reason}")
        print(f"     → images suivantes en fallback stock.")


def _endpoint() -> str:
    return (f"https://api.cloudflare.com/client/v4/accounts/"
            f"{CLOUDFLARE_ACCOUNT_ID}/ai/run/{MODEL}")


def generate_image(prompt: str, output_path: Path, seed: int | None = None) -> Path:
    """Génère une image via Cloudflare FLUX-1-schnell et l'écrit sur disque.

    Lève CloudflareUnavailable si le service est définitivement indisponible
    (le caller doit alors basculer en fallback stock).
    """
    if not is_configured():
        raise CloudflareUnavailable("Cloudflare non configuré (.env)")
    if _breaker.is_set():
        raise CloudflareUnavailable(f"Cloudflare indisponible ({_breaker_reason})")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    headers = {"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"}
    payload: dict = {"prompt": prompt[:2048], "steps": STEPS}
    if seed is not None:
        payload["seed"] = seed

    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        if _breaker.is_set():
            raise CloudflareUnavailable(f"Cloudflare indisponible ({_breaker_reason})")
        try:
            r = requests.post(_endpoint(), json=payload, headers=headers, timeout=TIMEOUT)

            # Erreurs DÉFINITIVES → circuit breaker, pas de retry.
            if r.status_code in (401, 403):
                _trip_breaker(f"HTTP {r.status_code} — token invalide ou accès refusé")
                raise CloudflareUnavailable(f"Cloudflare HTTP {r.status_code}")
            if r.status_code == 429:
                _trip_breaker("HTTP 429 — quota quotidien épuisé (revient demain)")
                raise CloudflareUnavailable("Cloudflare quota épuisé")

            r.raise_for_status()
            data = r.json()
            if not data.get("success", True):
                raise RuntimeError(f"Cloudflare erreur API : {data.get('errors')}")

            b64 = data.get("result", {}).get("image")
            if not b64:
                raise RuntimeError("Réponse Cloudflare sans champ image")
            content = base64.b64decode(b64)
            if len(content) < 1000:
                raise RuntimeError(f"Image trop petite ({len(content)} octets)")
            output_path.write_bytes(content)
            return output_path

        except CloudflareUnavailable:
            raise  # définitif : on propage sans retry
        except Exception as e:
            last_error = e
            wait = 3 * attempt
            print(f"  ⚠️  Cloudflare essai {attempt}/{MAX_RETRIES} échoué : {str(e)[:80]}")
            time.sleep(wait)

    raise RuntimeError(
        f"Cloudflare : échec après {MAX_RETRIES} essais : {last_error}"
    )
