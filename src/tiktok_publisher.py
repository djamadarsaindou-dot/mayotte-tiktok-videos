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

    r = requests.post(
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
    r = requests.post(url, json=json, data=data, headers=headers, timeout=60)
    if r.status_code == 401:
        # Token expiré → refresh + retry
        access_token = refresh_access_token()
        headers["Authorization"] = f"Bearer {access_token}"
        r = requests.post(url, json=json, data=data, headers=headers, timeout=60)
    return r


MAX_CHUNK = 64 * 1024 * 1024  # TikTok : chunk_size max 64 MB
MIN_CHUNK = 5 * 1024 * 1024   # TikTok : chunk_size min 5 MB


def _compute_chunks(size: int) -> tuple[int, int]:
    """Calcule (chunk_size, total_chunks) selon les règles strictes TikTok :
    - total_chunks = video_size // chunk_size (FLOOR division)
    - Le dernier chunk = chunk_size + (video_size - chunk_size * total_chunks)
      (donc il peut être plus gros que chunk_size, mais ≤ 2× chunk_size)
    - chunk_size doit être entre 5 MB et 64 MB
    - Pour ≤ 64 MB : 1 chunk de taille = video_size

    Stratégie : choisir le plus petit total tel que chunk_size = size//total ≤ 64 MB.
    """
    import math
    if size <= MAX_CHUNK:
        return size, 1
    total = math.ceil(size / MAX_CHUNK)
    chunk = size // total
    if chunk < MIN_CHUNK:
        total = max(1, size // MIN_CHUNK)
        chunk = size // total
    return chunk, total


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
            up = requests.put(
                upload_url,
                data=content,
                headers={
                    "Content-Type": "video/mp4",
                    "Content-Length": str(this_chunk),
                    "Content-Range": f"bytes {start}-{start+this_chunk-1}/{size}",
                },
                timeout=300,
            )
            # 206 = partial accepted, 200/201 = final accepted
            if up.status_code not in (200, 201, 206):
                raise RuntimeError(
                    f"TikTok upload chunk {i+1}/{total_chunks} HTTP {up.status_code}: "
                    f"{up.text[:400]}"
                )
            print(f"     chunk {i+1}/{total_chunks} ({this_chunk/1024/1024:.1f} MB) → "
                  f"HTTP {up.status_code}")

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
