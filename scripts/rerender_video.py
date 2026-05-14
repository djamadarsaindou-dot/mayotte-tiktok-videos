"""Re-monte une vidéo existante depuis son dossier temp/ sans refaire LLM/voix/visuels.

Usage :
    python scripts/rerender_video.py <slug-de-la-video>
    python scripts/rerender_video.py 20260504_084155_le-voulé-le-bbq-mahorais-qui-sent-locéan

Utile quand on a corrigé un bug de montage (ex: Ken Burns) et qu'on veut
régénérer la vidéo finale sans repasser 30 min sur LLM/TTS/Pollinations.
"""
import json
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ajoute la racine du projet au sys.path pour pouvoir importer `src`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import OUTPUT_DIR, TEMP_DIR, VISUALS_PER_SCENE
from src.editor import assemble_video, get_audio_duration


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage : python scripts/rerender_video.py <slug>")
        return 1

    slug = sys.argv[1]
    work_dir = TEMP_DIR / slug
    if not work_dir.exists():
        print(f"❌ Dossier temp introuvable : {work_dir}")
        return 1

    audio_path = work_dir / "voice.mp3"
    ass_path = work_dir / "subs.ass"
    if not audio_path.exists() or not ass_path.exists():
        print(f"❌ voice.mp3 ou subs.ass manquant dans {work_dir}")
        return 1

    # Récupère les métadonnées depuis le JSON
    meta_candidates = list(OUTPUT_DIR.glob(f"{slug}.json"))
    if not meta_candidates:
        print(f"❌ Pas de JSON {slug}.json dans output/")
        return 1
    meta = json.loads(meta_candidates[0].read_text(encoding="utf-8"))
    scenes = meta["scenes"]
    print(f"📝 {meta['title']} — {len(scenes)} scènes")

    # Reconstruit l'ordre des assets : asset_s{NN}_v{V}.{mp4|jpg}
    asset_paths: list[Path] = []
    for s_idx in range(len(scenes)):
        for v_idx in range(VISUALS_PER_SCENE):
            mp4 = work_dir / f"asset_s{s_idx:02d}_v{v_idx}.mp4"
            jpg = work_dir / f"asset_s{s_idx:02d}_v{v_idx}.jpg"
            if mp4.exists():
                asset_paths.append(mp4)
            elif jpg.exists():
                asset_paths.append(jpg)
            else:
                # fallback s'il y a un suffixe _fallback
                mp4f = work_dir / f"asset_s{s_idx:02d}_v{v_idx}_fallback.mp4"
                jpgf = work_dir / f"asset_s{s_idx:02d}_v{v_idx}_fallback.jpg"
                if mp4f.exists():
                    asset_paths.append(mp4f)
                elif jpgf.exists():
                    asset_paths.append(jpgf)
                else:
                    print(f"⚠️  Asset manquant scène {s_idx} visuel {v_idx}")

    expected = len(scenes) * VISUALS_PER_SCENE
    if len(asset_paths) != expected:
        print(f"⚠️  {len(asset_paths)} assets trouvés (attendu {expected})")

    # Calcule les durées (mêmes maths que generate_video.py)
    audio_duration = get_audio_duration(audio_path)
    word_counts = [len(s["narration"].split()) for s in scenes]
    total_words = sum(word_counts) or 1
    asset_durations: list[float] = []
    for s_idx in range(len(scenes)):
        scene_dur = audio_duration * (word_counts[s_idx] / total_words)
        per_visual = scene_dur / VISUALS_PER_SCENE
        for _ in range(VISUALS_PER_SCENE):
            asset_durations.append(per_visual)
    # Coupe si on a moins d'assets que prévu
    asset_durations = asset_durations[:len(asset_paths)]

    print(f"🔊 Audio : {audio_duration:.1f}s, {len(asset_paths)} clips × {asset_durations[0]:.2f}s")

    # Supprime les anciens clips/ pour partir propre
    clips_dir = work_dir / "clips"
    if clips_dir.exists():
        shutil.rmtree(clips_dir)
        print("🧹 Anciens clips/ supprimés")

    # Re-encode la vidéo finale
    output_path = OUTPUT_DIR / f"{slug}.mp4"
    print(f"🎞️  Re-montage vers {output_path.name}...")
    assemble_video(asset_paths, asset_durations, audio_path, ass_path, output_path, work_dir)
    print(f"\n✅ Re-rendu : {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
