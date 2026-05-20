"""Notifications Windows 10/11 (toast) quand une vidéo est prête.

Affiche une notification native avec :
- Titre + message
- Son court par défaut
- Bouton « Ouvrir le dossier » qui lance l'Explorateur
- Bouton « Voir » qui ouvre directement la vidéo

Tolérant aux erreurs : si winotify n'est pas dispo ou plante, on log et on
continue (la notif est un confort, pas une fonctionnalité critique).
"""
from __future__ import annotations

from pathlib import Path


def notify_video_ready(video_path: Path, caption_text: str | None = None) -> None:
    """Affiche une toast Windows annonçant la nouvelle vidéo."""
    try:
        from winotify import Notification, audio
    except Exception as e:
        print(f"  ℹ️  Notification skip (winotify indispo : {e})")
        return

    try:
        folder = video_path.parent
        title = "🎬 Nouvelle vidéo Mayotte"
        # Première ligne du caption pour le message si fourni, sinon titre fichier
        if caption_text:
            msg = caption_text.split("\n")[0][:120]
        else:
            msg = video_path.stem.replace("_", " ")[:120]

        toast = Notification(
            app_id="Mayotte TikTok Generator",
            title=title,
            msg=msg,
            duration="short",
        )
        toast.set_audio(audio.Default, loop=False)
        toast.add_actions(
            label="Ouvrir le dossier",
            launch=f"file:///{folder.as_posix()}/",
        )
        toast.add_actions(
            label="Voir la vidéo",
            launch=f"file:///{video_path.as_posix()}",
        )
        toast.show()
    except Exception as e:
        print(f"  ⚠️  Notification a échoué : {e}")
