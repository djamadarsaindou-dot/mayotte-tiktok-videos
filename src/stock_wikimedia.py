"""Recherche d'images Mayotte sur Wikimedia Commons (sans clé API).

API doc : https://commons.wikimedia.org/w/api.php
"""
import urllib.parse
from pathlib import Path

import requests

WIKI_API = "https://commons.wikimedia.org/w/api.php"
TIMEOUT = 30
# Wikimedia exige un User-Agent identifiant + un point de contact
HEADERS = {
    "User-Agent": "MayotteTikTokBot/1.0 (https://github.com/djamadarsaindou-dot/mayotte-tiktok-videos; educational)",
    "Accept": "application/json",
}


def search_image(query: str, output_path: Path, force_mayotte: bool = True) -> Path | None:
    """Cherche une image sur Wikimedia Commons et la télécharge.

    Si force_mayotte est vrai, ajoute « Mayotte » à la requête pour cibler
    le territoire mahorais.
    """
    full_query = f"{query} Mayotte" if force_mayotte else query
    try:
        r = requests.get(
            WIKI_API,
            params={
                "action": "query",
                "format": "json",
                "generator": "search",
                "gsrsearch": f"{full_query} filetype:bitmap",
                "gsrnamespace": "6",  # File namespace
                "gsrlimit": 8,
                "prop": "imageinfo",
                "iiprop": "url|size|mime",
                "iiurlheight": "1920",
            },
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  ⚠️  Wikimedia recherche échec '{query[:40]}' : {str(e)[:80]}")
        return None

    pages = (data.get("query", {}) or {}).get("pages", {}) or {}
    if not pages:
        return None

    # Tri : préférer celles dont la dimension est verticale ou carrée
    candidates = []
    for p in pages.values():
        info_list = p.get("imageinfo") or []
        if not info_list:
            continue
        info = info_list[0]
        url = info.get("thumburl") or info.get("url")
        mime = info.get("mime", "")
        if not url or not mime.startswith("image/"):
            continue
        if mime in ("image/svg+xml",):
            continue
        w = info.get("thumbwidth") or info.get("width") or 0
        h = info.get("thumbheight") or info.get("height") or 0
        # On veut grande résolution
        if w < 800 or h < 800:
            continue
        candidates.append((url, w, h))

    if not candidates:
        return None

    # Trie : priorité aux images les plus grandes
    candidates.sort(key=lambda c: -(c[1] * c[2]))

    for url, _, _ in candidates:
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            output_path.write_bytes(r.content)
            if output_path.stat().st_size > 50_000:
                return output_path
        except Exception as e:
            print(f"  ⚠️  Wikimedia download échec : {str(e)[:80]}")
            continue
    return None
