"""Scraper RSS pour les actualités Mayotte (sources officielles).

Sources :
- Mayotte la 1ère (France TV info)
- Le Journal de Mayotte
- Mayotte Hebdo
"""
import html
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone

from src.net import SESSION

RSS_FEEDS = [
    ("Mayotte la 1ère", "https://la1ere.francetvinfo.fr/mayotte/rss"),
    ("Le Journal de Mayotte", "https://lejournaldemayotte.yt/feed/"),
    ("Mayotte Hebdo", "https://www.mayottehebdo.com/feed/"),
]

TIMEOUT = 20
HEADERS = {"User-Agent": "Mozilla/5.0 (Mayotte TikTok generator)"}


@dataclass
class NewsItem:
    title: str
    description: str
    link: str
    source: str
    published: str

    def short(self) -> str:
        return f"[{self.source}] {self.title}"


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_feed(source: str, url: str) -> list[NewsItem]:
    try:
        r = SESSION.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        root = ET.fromstring(r.content)
    except Exception as e:
        print(f"  ⚠️  RSS {source} échec : {str(e)[:80]}")
        return []

    items: list[NewsItem] = []
    # RSS 2.0 et Atom
    for item in root.iter():
        tag = item.tag.split("}", 1)[-1].lower()
        if tag in ("item", "entry"):
            title = _strip_html(_first_text(item, ["title"]))
            link = _first_text(item, ["link"]) or _first_attr(item, ["link"], "href") or ""
            description = _strip_html(_first_text(item, ["description", "summary", "content"]))
            published = _first_text(item, ["pubdate", "updated", "published"]) or ""
            if title:
                items.append(NewsItem(
                    title=title[:200],
                    description=description[:500],
                    link=link.strip(),
                    source=source,
                    published=published.strip(),
                ))
    return items


def _first_text(parent, names: list[str]) -> str:
    names_lower = {n.lower() for n in names}
    for child in parent.iter():
        tag = child.tag.split("}", 1)[-1].lower()
        if tag in names_lower:
            return (child.text or "").strip()
    return ""


def _first_attr(parent, names: list[str], attr: str) -> str:
    names_lower = {n.lower() for n in names}
    for child in parent.iter():
        tag = child.tag.split("}", 1)[-1].lower()
        if tag in names_lower and child.attrib.get(attr):
            return child.attrib[attr]
    return ""


def fetch_recent_news(max_per_source: int = 8) -> list[NewsItem]:
    """Récupère les actus les plus récentes de toutes les sources."""
    all_items: list[NewsItem] = []
    for source, url in RSS_FEEDS:
        items = _parse_feed(source, url)
        all_items.extend(items[:max_per_source])
    return all_items


def pick_news_topic(news: list[NewsItem]) -> NewsItem | None:
    """Choisit une actu adaptée pour une vidéo TikTok.

    Évite les sujets trop polémiques/sensibles (mort, violence, justice).
    """
    if not news:
        return None
    forbidden = re.compile(
        r"\b(meurtre|tu[ée]|d[ée]c[èe]s|crime|viol\b|cadavre|vol|incendie|rixe|"
        r"agression|braquage|prison|tribunal|condamn|drogue|narco|arrestation)\b",
        re.IGNORECASE,
    )
    safe = [n for n in news if not forbidden.search(n.title + " " + n.description)]
    if not safe:
        return None
    # Préférence aux actus avec une description riche
    safe.sort(key=lambda n: -len(n.description))
    import random
    # Aléatoire dans le top 5 pour la variété
    pool = safe[:5] if len(safe) >= 5 else safe
    return random.choice(pool)
