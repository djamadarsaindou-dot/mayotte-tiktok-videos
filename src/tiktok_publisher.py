"""Publication TikTok via Content Posting API (mode INBOX = brouillon privé).

La vidéo arrive dans la boîte de réception TikTok de l'utilisateur. Il ouvre
l'app, voit le brouillon, et clique « Publier » pour finaliser.

Ce mode INBOX fonctionne avec une app TikTok **non-auditée** (pas besoin
d'attendre la validation par TikTok qui prend plusieurs semaines).

Pré-requis (variables d'environnement) :
    TIKTOK_CLIENT_KEY        — depuis l'app TikTok Developer
    TIKTOK_CLIENT_SECRET     — depuis l'app TikTok Developer
    TIKTOK_ACCESS_TOKEN      — obtenu via scripts/setup_tiktok.py
    TIKTOK_REFRESH_TOKEN     — obtenu via scripts/setup_tiktok.py

Auto-refresh : si l'access_token est expiré, on le refresh transparently
via le refresh_token, et on met à jour .env.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter

from src.net import SESSION

# Charge .env pour que ce module soit utilisable en standalone (tests, debug)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except Exception:
    pass

INBOX_INIT_URL = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"


def _env(name: str) -> str | None:
    v = os.getenv(name, "").strip()
    return v or None


def is_configured() -> bool:
    """Vrai si tous les secrets TikTok sont présents."""
    return all(_env(k) for k in (
        "TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET",
        "TIKTOK_ACCESS_TOKEN", "TIKTOK_REFRESH_TOKEN",
    ))


def update_env_vars(updates: dict[str, str]) -> None:
    """Met à jour les valeurs dans .env (préserve les autres lignes/commentaires)."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        env_path.write_text("\n".join(f"{k}={v}" for k, v in updates.items()) + "\n",
                            encoding="utf-8")
        return
    lines = env_path.read_text(encoding="utf-8").splitlines()
    keys_to_add = set(updates.keys())
    out: list[str] = []
    for line in lines:
        if "=" in line and not line.lstrip().startswith("#"):
            key = line.split("=", 1)[0].strip()
            if key in updates:
                out.append(f"{key}={updates[key]}")
                keys_to_add.discard(key)
                continue
        out.append(line)
    for k in keys_to_add:
        out.append(f"{k}={updates[k]}")
    env_path.write_text("\n".join(out) + "\n", encoding="utf-8")


def refresh_access_token() -> str:
    """Rafraîchit l'access_token via le refresh_token. Met à jour .env."""
    client_key = _env("TIKTOK_CLIENT_KEY")
    client_secret = _env("TIKTOK_CLIENT_SECRET")
    refresh_token = _env("TIKTOK_REFRESH_TOKEN")
    if not all([client_key, client_secret, refresh_token]):
        raise RuntimeError("TIKTOK_CLIENT_KEY/SECRET/REFRESH_TOKEN manquants dans .env")

    r = SESSION.post(
        TOKEN_URL,
        data={
            "client_key": client_key,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    if r.status_code != 200:
        raise RuntimeError(f"TikTok refresh HTTP {r.status_code}: {r.text[:300]}")
    data = r.json()
    if "access_token" not in data:
        raise RuntimeError(f"Refresh inattendu : {data}")

    new_access = data["access_token"]
    new_refresh = data.get("refresh_token", refresh_token)
    update_env_vars({
        "TIKTOK_ACCESS_TOKEN": new_access,
        "TIKTOK_REFRESH_TOKEN": new_refresh,
    })
    os.environ["TIKTOK_ACCESS_TOKEN"] = new_access
    os.environ["TIKTOK_REFRESH_TOKEN"] = new_refresh
    return new_access


def _post_with_auto_refresh(url: str, *, json=None, headers: dict | None = None,
                            data=None) -> requests.Response:
    """POST avec auto-refresh du token sur 401."""
    headers = dict(headers or {})
    access_token = _env("TIKTOK_ACCESS_TOKEN")
    if not access_token:
        access_token = refresh_access_token()
    headers["Authorization"] = f"Bearer {access_token}"
    r = SESSION.post(url, json=json, data=data, headers=headers, timeout=60)
    if r.status_code == 401:
        # Token expiré → refresh + retry
        access_token = refresh_access_token()
        headers["Authorization"] = f"Bearer {access_token}"
        r = SESSION.post(url, json=json, data=data, headers=headers, timeout=60)
    return r


MAX_CHUNK = 64 * 1024 * 1024  # TikTok : chunk_size max 64 MB
MIN_CHUNK = 5 * 1024 * 1024   # TikTok : chunk_size min 5 MB
# Petits chunks volontairement, pour résister aux connexions instables :
# si la liaison coupe en plein milieu d'un chunk, le retry n'a qu'un petit
# volume à reprendre — beaucoup plus robuste à Mayotte qu'un upload de 60 MB.
TARGET_CHUNK = 10 * 1024 * 1024  # 10 MB

# ---------------------------------------------------------------------------
# Session dédiée aux PUT de chunks — SANS retry automatique urllib3.
#
# Pourquoi : la session partagée src.net.SESSION retente TOUTES les méthodes
# (allowed_methods=None). Sur un PUT de chunk, si la RÉPONSE se perd (connexion
# Mayotte instable), urllib3 re-envoie silencieusement le MÊME PUT alors que
# TikTok a déjà stocké ces bytes → TikTok répond 416 (Range Not Satisfiable)
# au doublon, et l'upload était considéré comme échoué à tort.
# Ici : aucun retry urllib3 (max_retries=0) ; le retry est géré EXPLICITEMENT
# par _put_chunk, qui sait interpréter chaque cas (416 = déjà reçu, etc.).
# ---------------------------------------------------------------------------
_UPLOAD_SESSION = requests.Session()
_UPLOAD_SESSION.mount("https://", HTTPAdapter(max_retries=0))
_UPLOAD_SESSION.mount("http://", HTTPAdapter(max_retries=0))

# Retry explicite par chunk : 5 tentatives, attentes progressives entre deux
# essais (3/6/12/24 s) — le temps que la connexion revienne.
_CHUNK_MAX_ATTEMPTS = 5
_CHUNK_BACKOFF_S = (3, 6, 12, 24)

# Exceptions réseau transitoires : on retente le même chunk.
_RETRYABLE_EXCEPTIONS = (
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,
    requests.exceptions.ChunkedEncodingError,
)


def _compute_chunks(size: int) -> tuple[int, int]:
    """Calcule (chunk_size, total_chunks) selon les règles strictes TikTok :
    - total_chunks = video_size // chunk_size (FLOOR division)
    - Le dernier chunk = chunk_size + (video_size - chunk_size * total_chunks)
      (donc il peut être plus gros que chunk_size, mais ≤ 2× chunk_size)
    - chunk_size doit être entre 5 MB et 64 MB
    - Pour ≤ TARGET_CHUNK : 1 chunk de taille = video_size

    Stratégie : viser TARGET_CHUNK (10 MB) — petits chunks plus robustes
    sur connexion instable. Floor MIN_CHUNK appliqué si nécessaire.
    """
    import math
    if size <= TARGET_CHUNK:
        return size, 1
    total = math.ceil(size / TARGET_CHUNK)
    chunk = size // total
    if chunk < MIN_CHUNK:
        total = max(1, size // MIN_CHUNK)
        chunk = size // total
    return chunk, total


def _put_chunk(upload_url: str, content: bytes, *, start: int, total_size: int,
               index: int, total_chunks: int) -> None:
    """PUT d'un chunk avec retry EXPLICITE selon la sémantique de chaque cas.

    - Exception réseau (coupure, timeout) → on retente le MÊME chunk ;
    - HTTP 416 → TikTok a DÉJÀ reçu ces bytes (doublon après coupure de la
      réponse) → ce n'est PAS une erreur, on passe au chunk suivant ;
    - HTTP 429 / 5xx → transitoire, on retente avec backoff ;
    - HTTP 200/201/206 → chunk accepté ;
    - autres 4xx → erreur définitive (auth, requête invalide…), inutile de
      retenter : on échoue immédiatement.

    `content` est déjà en mémoire : en cas de retry, on re-PUT les mêmes bytes
    sans relire le fichier. Lève RuntimeError après épuisement des tentatives.
    """
    this_chunk = len(content)
    headers = {
        "Content-Type": "video/mp4",
        "Content-Length": str(this_chunk),
        "Content-Range": f"bytes {start}-{start + this_chunk - 1}/{total_size}",
    }
    last_error = "?"
    for attempt in range(1, _CHUNK_MAX_ATTEMPTS + 1):
        try:
            up = _UPLOAD_SESSION.put(
                upload_url,
                data=content,
                headers=headers,
                # Timeout court : sur connexion instable, mieux vaut échouer
                # vite et relancer nous-mêmes que bloquer 5 minutes sur une
                # socket en train de mourir.
                timeout=120,
            )
        except _RETRYABLE_EXCEPTIONS as exc:
            last_error = f"{type(exc).__name__}: {exc}"
        else:
            # 206 = partial accepted, 200/201 = final accepted
            if up.status_code in (200, 201, 206):
                print(f"     chunk {index}/{total_chunks} "
                      f"({this_chunk/1024/1024:.1f} MB) → HTTP {up.status_code}")
                return
            if up.status_code == 416:
                # Doublon : TikTok a déjà stocké ces bytes (le PUT précédent
                # était passé mais sa réponse s'est perdue). Tout va bien.
                print(f"     chunk {index}/{total_chunks} déjà reçu par TikTok "
                      f"(HTTP 416, doublon) → chunk suivant")
                return
            if up.status_code == 429 or up.status_code >= 500:
                last_error = f"HTTP {up.status_code}: {up.text[:200]}"
            else:
                # 4xx définitif : retenter ne changera rien.
                raise RuntimeError(
                    f"TikTok upload chunk {index}/{total_chunks} "
                    f"HTTP {up.status_code}: {up.text[:400]}"
                )
        if attempt >= _CHUNK_MAX_ATTEMPTS:
            break
        wait = _CHUNK_BACKOFF_S[min(attempt - 1, len(_CHUNK_BACKOFF_S) - 1)]
        print(f"     ⚠️ chunk {index}/{total_chunks} tentative "
              f"{attempt + 1}/{_CHUNK_MAX_ATTEMPTS} après {last_error} "
              f"— attente {wait}s")
        time.sleep(wait)
    raise RuntimeError(
        f"TikTok upload chunk {index}/{total_chunks} échoué après "
        f"{_CHUNK_MAX_ATTEMPTS} tentatives — dernière erreur : {last_error}"
    )


def publish_inbox(video_path: Path) -> dict:
    """Upload la vidéo en mode INBOX (brouillon privé).

    Retourne {'publish_id': str, 'status': str, 'video': str}.
    L'utilisateur doit ensuite ouvrir TikTok pour finaliser la publication.
    Gère le chunking automatique selon les contraintes TikTok (5 MB ≤ chunk ≤ 64 MB).
    """
    if not video_path.exists():
        raise FileNotFoundError(video_path)

    size = video_path.stat().st_size
    chunk_size, total_chunks = _compute_chunks(size)

    init_body = {
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": size,
            "chunk_size": chunk_size,
            "total_chunk_count": total_chunks,
        }
    }

    print(f"  🚀 TikTok : init upload ({size/1024/1024:.1f} MB en {total_chunks} chunk(s))...")
    r = _post_with_auto_refresh(
        INBOX_INIT_URL,
        json=init_body,
        headers={"Content-Type": "application/json; charset=UTF-8"},
    )
    if r.status_code != 200:
        raise RuntimeError(f"TikTok init HTTP {r.status_code}: {r.text[:400]}")
    data = r.json().get("data", {})
    publish_id = data.get("publish_id")
    upload_url = data.get("upload_url")
    if not publish_id or not upload_url:
        raise RuntimeError(f"Réponse TikTok inattendue : {data}")

    print(f"  ⬆️  TikTok : upload...")
    with video_path.open("rb") as f:
        for i in range(total_chunks):
            start = i * chunk_size
            # Tous les chunks font chunk_size SAUF le dernier qui prend le reste
            # (peut être plus gros que chunk_size, c'est la règle TikTok)
            this_chunk = chunk_size if i < total_chunks - 1 else size - start
            content = f.read(this_chunk)
            # PUT via la session dédiée SANS retry urllib3 : le retry est
            # explicite dans _put_chunk (416 = déjà reçu → on continue).
            _put_chunk(
                upload_url, content,
                start=start, total_size=size,
                index=i + 1, total_chunks=total_chunks,
            )

    # Petit poll de statut (best-effort)
    time.sleep(2)
    status = "uploaded"
    try:
        s = _post_with_auto_refresh(
            STATUS_URL,
            json={"publish_id": publish_id},
            headers={"Content-Type": "application/json; charset=UTF-8"},
        )
        if s.status_code == 200:
            status = s.json().get("data", {}).get("status", "uploaded")
    except Exception:
        pass

    print(f"  ✅ TikTok : vidéo dans la boîte de réception (publish_id={publish_id[:12]}…)")
    print("  📱 Ouvre l'app TikTok pour finaliser la publication (1 clic)")

    return {"publish_id": publish_id, "status": status, "video": video_path.name}
