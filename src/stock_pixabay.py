"""Recherche de vidéos / photos sur Pixabay (gratuit, clé API requise).

API doc : https://pixabay.com/api/docs/
"""
import time
from pathlib import Path

from src.config import PIXABAY_API_KEY
from src.net import SESSION

PIXABAY_VIDEOS = "https://pixabay.com/api/videos/"
PIXABAY_IMAGES = "https://pixabay.com/api/"
TIMEOUT = 60


def _pick_video_file(video: dict) -> tuple[str, int, int] | None:
    """Choisit le meilleur fichier (medium 960p ou large) avec ses dimensions."""
    files = video.get("videos", {})
    for key in ("medium", "large", "small", "tiny"):
        v = files.get(key)
        if v and v.get("url"):
            return v["url"], v.get("width", 0), v.get("height", 0)
    return None


def search_video(query: str, output_path: Path, min_duration: float = 3.0) -> Path | None:
    if not PIXABAY_API_KEY:
        return None

    try:
        r = SESSION.get(
            PIXABAY_VIDEOS,
            params={
                "key": PIXABAY_API_KEY,
                "q": query,
                "video_type": "all",
                "per_page": 10,
                "safesearch": "true",
            },
            timeout=TIMEOUT,
        )
        if r.status_code == 429:
            time.sleep(5)
            r = SESSION.get(PIXABAY_VIDEOS, params={"key": PIXABAY_API_KEY, "q": query, "per_page": 5}, timeout=TIMEOUT)
        r.raise_for_status()
        videos = r.json().get("hits", [])
    except Exception as e:
        print(f"  ⚠️  Pixabay vidéo échec '{query[:40]}' : {str(e)[:80]}")
        return None

    candidates = [v for v in videos if v.get("duration", 0) >= min_duration]
    pool = candidates if candidates else videos
    if not pool:
        return None

    for video in pool:
        chosen = _pick_video_file(video)
        if not chosen:
            continue
        url, _, _ = chosen
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with SESSION.get(url, stream=True, timeout=TIMEOUT) as dl:
                dl.raise_for_status()
                with output_path.open("wb") as f:
                    for chunk in dl.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)
            if output_path.stat().st_size > 50_000:
                return output_path
        except Exception as e:
            print(f"  ⚠️  Pixabay download échec : {str(e)[:80]}")
            continue
    return None


def search_photo(query: str, output_path: Path) -> Path | None:
    if not PIXABAY_API_KEY:
        return None

    try:
        r = SESSION.get(
            PIXABAY_IMAGES,
            params={
                "key": PIXABAY_API_KEY,
                "q": query,
                "image_type": "photo",
                "orientation": "vertical",
                "per_page": 10,
                "safesearch": "true",
                "min_width": 1080,
            },
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        photos = r.json().get("hits", [])
    except Exception:
        return None

    for photo in photos:
        url = photo.get("largeImageURL") or photo.get("webformatURL")
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
