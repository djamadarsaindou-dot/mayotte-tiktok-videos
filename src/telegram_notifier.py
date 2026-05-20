"""Notification Telegram quand un brouillon TikTok est prêt à publier.

Permet de recevoir une notif push sur ton téléphone (gratuit, instantané)
avec un bouton « Ouvrir TikTok » qui lance directement l'app sur la boîte
de réception. Plus besoin d'ouvrir le PC pour vérifier.

Setup :
1. Sur Telegram, parler à @BotFather → /newbot → suivre les instructions
   → récupérer le TOKEN du bot (genre `123456:ABC-DEF...`)
2. Démarrer une conversation avec ton bot (clic « Start » sur sa page)
3. Récupérer ton chat_id en visitant cette URL dans un navigateur :
   https://api.telegram.org/bot<TOKEN>/getUpdates
   → champ `chat.id` dans la réponse JSON
4. Ajouter dans .env :
   TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
   TELEGRAM_CHAT_ID=123456789

Le module est best-effort : si Telegram échoue, on log mais on ne casse
pas le pipeline.
"""
from __future__ import annotations

import os
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except Exception:
    pass

API_BASE = "https://api.telegram.org"


def _env(name: str) -> str | None:
    v = os.getenv(name, "").strip()
    return v or None


def is_configured() -> bool:
    """Vrai si le bot Telegram est configuré."""
    return bool(_env("TELEGRAM_BOT_TOKEN") and _env("TELEGRAM_CHAT_ID"))


def send_draft_ready(video_name: str, caption: str, publish_id: str | None = None) -> bool:
    """Envoie une notif Telegram avec un bouton pour ouvrir TikTok.

    Retourne True si envoyé avec succès, False sinon (best-effort).
    """
    token = _env("TELEGRAM_BOT_TOKEN")
    chat_id = _env("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False

    # Tronque la caption pour ne pas dépasser la limite Telegram (4096 chars)
    short_caption = caption.strip()
    if len(short_caption) > 500:
        short_caption = short_caption[:500] + "..."

    text = (
        f"🎬 *Nouvelle vidéo prête à publier*\n\n"
        f"📁 `{video_name}`\n\n"
        f"📝 *Caption :*\n{short_caption}\n\n"
        f"👉 Ouvre TikTok → Boîte de réception → 1 clic pour publier"
    )

    # Boutons : ouvrir l'app TikTok (deep link) + lien web fallback
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "📱 Ouvrir TikTok", "url": "https://www.tiktok.com/inbox"},
            ],
        ]
    }

    try:
        r = requests.post(
            f"{API_BASE}/bot{token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
                "reply_markup": reply_markup,
                "disable_web_page_preview": True,
            },
            timeout=15,
        )
        if r.status_code == 200:
            print(f"  📲 Telegram : notif envoyée")
            return True
        else:
            print(f"  ⚠️  Telegram HTTP {r.status_code}: {r.text[:200]}")
            return False
    except Exception as e:
        print(f"  ⚠️  Telegram échoué : {e}")
        return False


def send_error(message: str) -> bool:
    """Envoie une notif d'erreur (utile pour debug du cron)."""
    token = _env("TELEGRAM_BOT_TOKEN")
    chat_id = _env("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False
    try:
        r = requests.post(
            f"{API_BASE}/bot{token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": f"❌ *Erreur génération vidéo*\n\n```\n{message[:1500]}\n```",
                "parse_mode": "Markdown",
            },
            timeout=15,
        )
        return r.status_code == 200
    except Exception:
        return False
