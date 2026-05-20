"""Couche d'abstraction LLM : Mistral (préféré), Gemini, ou Groq.

API unique :
  - chat(system, user, json=False, temperature=0.85) -> str
  - chat_json(system, user, temperature=0.85) -> dict

Choix du provider :
  - LLM_PROVIDER=auto (défaut) → Mistral > Gemini > Groq selon les clés disponibles
  - LLM_PROVIDER=mistral|gemini|groq → forcé
"""
from __future__ import annotations

import json
from typing import Any

from src.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
    LLM_PROVIDER,
    MISTRAL_API_KEY,
    MISTRAL_MODEL,
)

_provider: str | None = None
_groq_client = None
_gemini_client = None
_mistral_client = None


def _resolve_provider() -> str:
    global _provider
    if _provider is not None:
        return _provider
    if LLM_PROVIDER == "mistral":
        if not MISTRAL_API_KEY:
            raise RuntimeError("LLM_PROVIDER=mistral mais MISTRAL_API_KEY manquant")
        _provider = "mistral"
    elif LLM_PROVIDER == "gemini":
        if not GEMINI_API_KEY:
            raise RuntimeError("LLM_PROVIDER=gemini mais GEMINI_API_KEY manquant")
        _provider = "gemini"
    elif LLM_PROVIDER == "groq":
        if not GROQ_API_KEY:
            raise RuntimeError("LLM_PROVIDER=groq mais GROQ_API_KEY manquant")
        _provider = "groq"
    else:  # auto
        if MISTRAL_API_KEY:
            _provider = "mistral"
        elif GEMINI_API_KEY:
            _provider = "gemini"
        elif GROQ_API_KEY:
            _provider = "groq"
        else:
            raise RuntimeError("Aucune clé LLM configurée (MISTRAL_API_KEY, GEMINI_API_KEY ou GROQ_API_KEY)")
    return _provider


def get_provider() -> str:
    return _resolve_provider()


def get_model_label() -> str:
    p = _resolve_provider()
    if p == "mistral":
        return f"Mistral ({MISTRAL_MODEL})"
    if p == "gemini":
        return f"Gemini ({GEMINI_MODEL})"
    return f"Groq ({GROQ_MODEL})"


# --- Mistral (via REST direct, OpenAI-compatible) ---

MISTRAL_ENDPOINT = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_MIN_INTERVAL = 2.0  # secondes entre 2 requêtes (free tier ~1 req/sec, marge)
_last_mistral_call: float = 0.0


def _throttle_mistral() -> None:
    import time
    global _last_mistral_call
    elapsed = time.time() - _last_mistral_call
    if elapsed < MISTRAL_MIN_INTERVAL:
        time.sleep(MISTRAL_MIN_INTERVAL - elapsed)
    _last_mistral_call = time.time()


def _chat_mistral(system: str, user: str, json_mode: bool, temperature: float) -> str:
    import time

    import requests
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    body: dict[str, Any] = {
        "model": MISTRAL_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": 8000,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}

    # Retry avec backoff sur 429
    for attempt in range(4):
        _throttle_mistral()
        r = requests.post(MISTRAL_ENDPOINT, headers=headers, json=body, timeout=120)
        if r.status_code == 200:
            data = r.json()
            return (data["choices"][0]["message"]["content"] or "").strip()
        if r.status_code == 429:
            wait = 2.0 + attempt * 2.0
            time.sleep(wait)
            continue
        raise RuntimeError(f"Mistral HTTP {r.status_code}: {r.text[:300]}")
    raise RuntimeError("Mistral 429 persistant après 4 tentatives")


# --- Groq ---

def _get_groq():
    global _groq_client
    if _groq_client is None:
        from groq import Groq
        _groq_client = Groq(api_key=GROQ_API_KEY)
    return _groq_client


def _chat_groq(system: str, user: str, json_mode: bool, temperature: float) -> str:
    client = _get_groq()
    kwargs: dict[str, Any] = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": 8000,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content.strip()


# --- Gemini ---

def _get_gemini():
    global _gemini_client
    if _gemini_client is None:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        _gemini_client = genai
    return _gemini_client


def _chat_gemini(system: str, user: str, json_mode: bool, temperature: float) -> str:
    genai = _get_gemini()
    config: dict[str, Any] = {
        "temperature": temperature,
        "max_output_tokens": 4000,
    }
    if json_mode:
        config["response_mime_type"] = "application/json"
    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=system,
        generation_config=config,
    )
    response = model.generate_content(user)
    return (response.text or "").strip()


# --- Dispatch ---

_BACKENDS = {
    "mistral": (lambda: bool(MISTRAL_API_KEY), _chat_mistral),
    "gemini": (lambda: bool(GEMINI_API_KEY), _chat_gemini),
    "groq": (lambda: bool(GROQ_API_KEY), _chat_groq),
}


def _model_for(name: str) -> str:
    if name == "mistral": return MISTRAL_MODEL
    if name == "gemini": return GEMINI_MODEL
    return GROQ_MODEL


def chat(system: str, user: str, json_mode: bool = False, temperature: float = 0.85) -> str:
    primary = _resolve_provider()
    last_err: Exception | None = None

    # Cache hit ? On essaye d'abord sans payer l'appel
    try:
        from src.llm_cache import get as _cache_get
        cached = _cache_get(primary, _model_for(primary), system, user, json_mode, temperature)
        if cached is not None:
            return cached
    except Exception:
        pass

    try:
        result = _BACKENDS[primary][1](system, user, json_mode, temperature)
        try:
            from src.llm_cache import put as _cache_put
            _cache_put(primary, _model_for(primary), system, user, json_mode, temperature, result)
        except Exception:
            pass
        return result
    except Exception as e:
        last_err = e
        print(f"  ⚠️  LLM {primary} a échoué : {str(e)[:120]}")

    # Fallback : essaye toujours les autres providers configurés en cas d'échec.
    for name, (has_key, fn) in _BACKENDS.items():
        if name == primary or not has_key():
            continue
        try:
            print(f"  ↪  Fallback sur {name}")
            result = fn(system, user, json_mode, temperature)
            try:
                from src.llm_cache import put as _cache_put
                _cache_put(name, _model_for(name), system, user, json_mode, temperature, result)
            except Exception:
                pass
            return result
        except Exception as e2:
            last_err = e2
            print(f"  ⚠️  Fallback {name} a aussi échoué : {str(e2)[:120]}")

    raise RuntimeError(f"Tous les providers LLM ont échoué : {last_err}")


def chat_json(system: str, user: str, temperature: float = 0.85) -> dict:
    raw = chat(system, user, json_mode=True, temperature=temperature)
    return json.loads(raw)
