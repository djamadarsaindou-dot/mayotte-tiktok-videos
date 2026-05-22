"""Recherche de vidéos B-roll sur Pexels (gratuit, clé API requise).

Renvoie des chemins vers des fichiers .mp4 téléchargés en local. Si Pexels
n'a pas de résultat ou si la clé API n'est pas configurée, renvoie None.
"""
import time
from pathlib import Path

from src.config import PEXELS_API_KEY
from src.net import SESSION

PEXELS_VIDEOS = "https://api.pexels.com/videos/search"
PEXELS_PHOTOS = "https://api.pexels.com/v1/search"
TIMEOUT = 60


def _headers() -> dict:
    return {"Authorization": PEXELS_API_KEY}


def _pick_vertical_file(video_files: list[dict]) -> dict | None:
    """Choisit le meilleur fichier : vertical de préférence, sinon le plus grand."""
    if not video_files:
        return None
    candidates = [f for f in video_files if f.get("file_type") == "video/mp4"]
    if not candidates:
        return None
    vertical = [f for f in candidates if f.get("height", 0) >= f.get("width", 0)]
    pool = vertical if vertical else candidates
    pool.sort(key=lambda f: (f.get("height", 0), f.get("width", 0)), reverse=True)
    return pool[0]


def search_video(query: str, output_path: Path, min_duration: float = 4.0) -> Path | None:
    """Cherche une vidéo B-roll sur Pexels et la télécharge.

    Renvoie le chemin local du .mp4 ou None en cas d'échec.
    """
    if not PEXELS_API_KEY:
        return None

    try:
        r = SESSION.get(
            PEXELS_VIDEOS,
            headers=_headers(),
            params={
                "query": query,
                "orientation": "portrait",
                "size": "medium",
                "per_page": 8,
            },
            timeout=TIMEOUT,
        )
        if r.status_code == 429:
            time.sleep(5)
            r = SESSION.get(PEXELS_VIDEOS, headers=_headers(),
                             params={"query": query, "orientation": "portrait", "per_page": 5},
                             timeout=TIMEOUT)
        r.raise_for_status()
        videos = r.json().get("videos", [])
    except Exception as e:
        print(f"  ⚠️  Pexels recherche échouée pour '{query[:40]}...' : {str(e)[:80]}")
        return None

    candidates = [v for v in videos if v.get("duration", 0) >= min_duration]
    pool = candidates if candidates else videos
    if not pool:
        return None

    for video in pool:
        chosen = _pick_vertical_file(video.get("video_files", []))
        if not chosen:
            continue
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with SESSION.get(chosen["link"], stream=True, timeout=TIMEOUT) as dl:
                dl.raise_for_status()
                with output_path.open("wb") as f:
                    for chunk in dl.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)
            if output_path.stat().st_size > 50_000:
                return output_path
        except Exception as e:
            print(f"  ⚠️  Téléchargement Pexels échoué : {str(e)[:80]}")
            continue

    return None


def search_photo(query: str, output_path: Path) -> Path | None:
    """Fallback : photo Pexels si pas de vidéo trouvée."""
    if not PEXELS_API_KEY:
        return None

    try:
        r = SESSION.get(
            PEXELS_PHOTOS,
            headers=_headers(),
            params={"query": query, "orientation": "portrait", "per_page": 5},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        photos = r.json().get("photos", [])
    except Exception:
        return None

    for photo in photos:
        url = photo.get("src", {}).get("portrait") or photo.get("src", {}).get("large2x")
        if not url:
            continue
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            r = SESSION.get(url, timeout=TIMEOUT)
            r.raise_for_status()
            output_path.write_bytes(r.content)
            return output_path
        except Exception:
            continue

    return None
