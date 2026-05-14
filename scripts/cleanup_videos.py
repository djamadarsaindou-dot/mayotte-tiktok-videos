"""Nettoie les vidéos pour éviter de saturer le disque.

- Garde les N dernières vidéos dans le dossier final (~/Videos/Mayotte TikTok)
- Garde les N dernières dans output/ du projet
- Supprime les dossiers temp/ qui n'ont plus de mp4 associé (les assets bruts
  pèsent ~2 GB par run, on les vire après que la vidéo finale soit prête)
"""
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import FINAL_VIDEOS_DIR, KEEP_LAST_N_VIDEOS, OUTPUT_DIR, TEMP_DIR


def trim_videos(folder: Path, label: str) -> None:
    if not folder.exists():
        return
    videos = sorted(folder.glob("*.mp4"),
                    key=lambda p: p.stat().st_mtime, reverse=True)
    print(f"🧹 {label} : {len(videos)} vidéos, on garde {KEEP_LAST_N_VIDEOS}")
    if len(videos) <= KEEP_LAST_N_VIDEOS:
        print("   Rien à supprimer.")
        return
    deleted = 0
    freed = 0
    for v in videos[KEEP_LAST_N_VIDEOS:]:
        json_p = v.with_suffix(".json")
        size = v.stat().st_size
        try:
            v.unlink()
            deleted += 1
            freed += size
            if json_p.exists():
                json_p.unlink()
        except Exception as e:
            print(f"   ⚠️  {v.name} : {e}")
    print(f"   ✓ {deleted} supprimées, {freed/1024/1024/1024:.2f} GB libérés")


def trim_temp() -> None:
    if not TEMP_DIR.exists():
        return
    temp_dirs = [d for d in TEMP_DIR.iterdir() if d.is_dir()]
    print(f"🧹 temp/ : {len(temp_dirs)} dossiers — suppression de tous sauf le plus récent")
    if not temp_dirs:
        return
    temp_dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
    # On garde le plus récent (peut être en cours), on supprime les autres
    freed = 0
    deleted = 0
    for d in temp_dirs[1:]:
        try:
            size_before = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
            shutil.rmtree(d)
            freed += size_before
            deleted += 1
        except Exception as e:
            print(f"   ⚠️  {d.name} : {e}")
    print(f"   ✓ {deleted} dossiers supprimés, {freed/1024/1024/1024:.2f} GB libérés")


def main() -> int:
    trim_videos(FINAL_VIDEOS_DIR, f"Dossier final ({FINAL_VIDEOS_DIR})")
    trim_videos(OUTPUT_DIR, f"output/ du projet")
    trim_temp()
    return 0


if __name__ == "__main__":
    sys.exit(main())
