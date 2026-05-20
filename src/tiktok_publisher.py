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


def publish_inbox(video_path: Path) -> dict:
    """Upload la vidéo en mode INBOX (brouillon privé).

    Retourne {'publish_id': str, 'status': str, 'video': str}.
    L'utilisateur doit ensuite ouvrir TikTok pour finaliser la publication.
    """
    if not video_path.exists():
        raise FileNotFoundError(video_path)

    size = video_path.stat().st_size
    init_body = {
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": size,
            "chunk_size": size,
            "total_chunk_count": 1,
        }
    }

    print(f"  🚀 TikTok : init upload ({size/1024/1024:.1f} MB)...")
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

    print(f"  ⬆️  TikTok : upload du fichier...")
    with video_path.open("rb") as f:
        content = f.read()
    up = requests.put(
        upload_url,
        data=content,
        headers={
            "Content-Type": "video/mp4",
            "Content-Length": str(size),
            "Content-Range": f"bytes 0-{size-1}/{size}",
        },
        timeout=300,
    )
    if up.status_code not in (200, 201):
        raise RuntimeError(f"TikTok upload HTTP {up.status_code}: {up.text[:400]}")

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
