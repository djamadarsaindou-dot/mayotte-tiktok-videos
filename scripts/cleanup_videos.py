"""Garde les N vidéos les plus récentes dans output/, supprime les autres.

Configurable via KEEP_LAST_N_VIDEOS dans .env (défaut : 50).
Logge ce qui est supprimé pour qu'on garde une trace.
"""
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.config import KEEP_LAST_N_VIDEOS, OUTPUT_DIR


def main() -> int:
    if not OUTPUT_DIR.exists():
        return 0

    videos = sorted(
        OUTPUT_DIR.glob("*.mp4"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    print(f"🧹 Nettoyage : {len(videos)} vidéos, on garde les {KEEP_LAST_N_VIDEOS} plus récentes")

    if len(videos) <= KEEP_LAST_N_VIDEOS:
        print("   Rien à supprimer.")
        return 0

    deleted = 0
    freed = 0
    for v in videos[KEEP_LAST_N_VIDEOS:]:
        json_p = v.with_suffix(".json")
        size = v.stat().st_size
        try:
            v.unlink()
            deleted += 1
            freed += size
            print(f"   ✗ {v.name} ({size/1024/1024:.0f} MB)")
            if json_p.exists():
                json_p.unlink()
        except Exception as e:
            print(f"   ⚠️  {v.name} : {e}")

    print(f"   ✓ {deleted} vidéos supprimées, {freed/1024/1024/1024:.2f} GB libérés")
    return 0


if __name__ == "__main__":
    sys.exit(main())
