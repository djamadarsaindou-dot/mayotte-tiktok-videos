"""Cache disque pour les appels LLM (Mistral / Groq / Gemini).

Stocke (provider, modèle, prompt système, prompt user, json_mode, temperature)
→ réponse, dans `output/llm_cache/` sous forme de petits fichiers JSON.

Permet d'économiser des appels API si une requête EXACTEMENT identique
est refaite (utile pour les re-rendus, les tests, ou en cas de relance après
crash en plein milieu d'une génération).

Le cache expire après CACHE_TTL_SECONDS pour ne pas servir des réponses obsolètes.
"""
import hashlib
import json
import time
from pathlib import Path

from src.config import OUTPUT_DIR

CACHE_DIR = OUTPUT_DIR / "llm_cache"
CACHE_TTL_SECONDS = 30 * 24 * 3600  # 30 jours


def _hash_key(provider: str, model: str, system: str, user: str,
              json_mode: bool, temperature: float) -> str:
    payload = json.dumps(
        {
            "p": provider, "m": model, "s": system, "u": user,
            "j": bool(json_mode), "t": round(float(temperature), 3),
        },
        ensure_ascii=False, sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def get(provider: str, model: str, system: str, user: str,
        json_mode: bool, temperature: float) -> str | None:
    """Renvoie la réponse cachée ou None si absente / expirée."""
    if not CACHE_DIR.exists():
        return None
    key = _hash_key(provider, model, system, user, json_mode, temperature)
    f = CACHE_DIR / f"{key}.json"
    if not f.exists():
        return None
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        if time.time() - data.get("ts", 0) > CACHE_TTL_SECONDS:
            f.unlink(missing_ok=True)
            return None
        return data.get("response")
    except Exception:
        return None


def put(provider: str, model: str, system: str, user: str,
        json_mode: bool, temperature: float, response: str) -> None:
    """Sauvegarde la réponse dans le cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = _hash_key(provider, model, system, user, json_mode, temperature)
    f = CACHE_DIR / f"{key}.json"
    try:
        f.write_text(
            json.dumps(
                {"ts": time.time(), "response": response,
                 "provider": provider, "model": model},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    except Exception:
        pass  # cache best-effort, jamais bloquant


def stats() -> dict:
    """Stats utiles : nb d'entrées + taille totale."""
    if not CACHE_DIR.exists():
        return {"entries": 0, "size_mb": 0.0}
    files = list(CACHE_DIR.glob("*.json"))
    total = sum(f.stat().st_size for f in files)
    return {"entries": len(files), "size_mb": round(total / 1024 / 1024, 2)}
