"""Session HTTP résiliente — retries automatiques face aux connexions instables.

À Mayotte, la connexion internet est souvent intermittente : elle coupe puis
revient au bout de quelques secondes. Une requête HTTP simple échoue dès le
premier hoquet. Cette session retente automatiquement, avec une attente
progressive, le temps que la connexion se rétablisse.

Couvre : connexion refusée/coupée, lecture interrompue, timeouts, et les
statuts serveur transitoires (429 trop de requêtes, 500/502/503/504).

Usage — remplace `requests` :
    from src.net import SESSION
    r = SESSION.get(url, timeout=60)
    r = SESSION.post(url, json=..., timeout=120)
"""
from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter

try:
    from urllib3.util.retry import Retry
except Exception:  # pragma: no cover - urllib3 toujours présent avec requests
    Retry = None


# Patience : 5 tentatives, backoff_factor=3 → attentes ~0/6/12/24/48 s entre
# les essais (plafonnées). Cumulé, ~90 s pour qu'une connexion instable revienne.
_TOTAL_RETRIES = 5
_BACKOFF_FACTOR = 3
_RETRY_STATUSES = (429, 500, 502, 503, 504)


def _build_retry():
    if Retry is None:
        return None
    kwargs = dict(
        total=_TOTAL_RETRIES,
        connect=_TOTAL_RETRIES,
        read=_TOTAL_RETRIES,
        backoff_factor=_BACKOFF_FACTOR,
        status_forcelist=_RETRY_STATUSES,
        raise_on_status=False,
    )
    # allowed_methods=None → retente toutes les méthodes (y compris POST, utile
    # pour la génération d'images Cloudflare). Compat anciennes versions urllib3.
    try:
        return Retry(allowed_methods=None, **kwargs)
    except TypeError:
        return Retry(method_whitelist=None, **kwargs)


def make_session() -> requests.Session:
    """Crée une session requests avec retry automatique sur erreurs réseau."""
    session = requests.Session()
    retry = _build_retry()
    if retry is not None:
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
    return session


# Session partagée par tout le projet (thread-safe pour des requêtes simples).
SESSION = make_session()


def get(url: str, **kwargs):
    """Raccourci : SESSION.get avec retries automatiques."""
    return SESSION.get(url, **kwargs)


def post(url: str, **kwargs):
    """Raccourci : SESSION.post avec retries automatiques."""
    return SESSION.post(url, **kwargs)
