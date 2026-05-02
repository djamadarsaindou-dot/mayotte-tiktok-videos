"""Script principal : génère une vidéo TikTok complète."""
import argparse
import json
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from src.config import OUTPUT_DIR, PEXELS_API_KEY, TEMP_DIR, VIDEO_HEIGHT, VIDEO_WIDTH
from src.editor import assemble_video, get_audio_duration
from src.images import generate_image
from src.script_writer import generate_script
from src.stock_videos import search_photo, search_video
from src.subtitles import build_karaoke_ass
from src.topics import TOPICS, random_topic
from src.voice import synthesize


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return text[:50] or "video"


def fetch_scene_asset(scene: dict, index: int, work_dir: Path) -> Path:
    """Pour une scène donnée, essaie Pexels (vidéo → photo) puis fallback Pollinations."""
    query = scene.get("search_query") or scene.get("image_prompt", "")
    img_prompt = scene["image_prompt"] + ", cinematic, vertical 9:16, no text"

    if PEXELS_API_KEY:
        video_path = work_dir / f"asset_{index:02d}.mp4"
        if search_video(query, video_path):
            print(f"   🎥 [{index+1}] Pexels video : {query[:50]}")
            return video_path
        photo_path = work_dir / f"asset_{index:02d}.jpg"
        if search_photo(query, photo_path):
            print(f"   📷 [{index+1}] Pexels photo : {query[:50]}")
            return photo_path

    img_path = work_dir / f"asset_{index:02d}.jpg"
    print(f"   🎨 [{index+1}] Pollinations IA : {scene['image_prompt'][:50]}...")
    seed = random.randint(1, 1_000_000)
    generate_image(img_prompt, img_path, seed=seed)
    return img_path


def build_video(topic_key: str | None = None) -> Path:
    if topic_key and topic_key in TOPICS:
        topic_def = TOPICS[topic_key]
    else:
        topic_key, topic_def = random_topic()

    print(f"\n🎬 Thème : {topic_def['label']}")
    print("📝 Génération du scénario via Groq...")
    script = generate_script(topic_def)
    print(f"   Titre : {script.get('title', '(sans titre)')}")
    print(f"   {len(script['scenes'])} scènes")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = slugify(script.get("title", topic_key))
    work_dir = TEMP_DIR / f"{timestamp}_{slug}"
    work_dir.mkdir(parents=True, exist_ok=True)

    full_text = " ".join(s["narration"].strip() for s in script["scenes"])
    audio_path = work_dir / "voice.mp3"

    print("🔊 Synthèse vocale (Edge-TTS, voix masculine)...")
    words = synthesize(full_text, audio_path)
    audio_duration = get_audio_duration(audio_path)
    print(f"   Durée audio : {audio_duration:.1f}s | {len(words)} mots avec timing")

    ass_path = work_dir / "subs.ass"
    build_karaoke_ass(words, ass_path, VIDEO_WIDTH, VIDEO_HEIGHT)

    src_label = "Pexels (vidéos/photos) → Pollinations" if PEXELS_API_KEY else "Pollinations IA uniquement"
    print(f"🎨 Récupération des {len(script['scenes'])} assets ({src_label})...")
    asset_paths: list[Path] = []
    for i, scene in enumerate(script["scenes"]):
        asset_paths.append(fetch_scene_asset(scene, i, work_dir))

    word_counts = [len(s["narration"].split()) for s in script["scenes"]]
    total_words = sum(word_counts) or 1
    scene_durations = [audio_duration * (w / total_words) for w in word_counts]

    output_path = OUTPUT_DIR / f"{timestamp}_{slug}.mp4"
    print("🎞️  Montage final...")
    assemble_video(asset_paths, scene_durations, audio_path, ass_path, output_path, work_dir)

    meta_path = OUTPUT_DIR / f"{timestamp}_{slug}.json"
    meta_path.write_text(
        json.dumps({
            "title": script.get("title"),
            "topic": topic_key,
            "topic_label": topic_def["label"],
            "hook": script.get("hook"),
            "scenes": script["scenes"],
            "duration": audio_duration,
            "word_count": total_words,
            "voice": "fr-FR-HenriNeural",
            "uses_pexels": bool(PEXELS_API_KEY),
            "created_at": datetime.now().isoformat(),
            "video_file": output_path.name,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\n✅ Vidéo prête : {output_path}")
    print(f"   Durée : {audio_duration:.1f}s | {total_words} mots")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Génère une vidéo TikTok automatiquement")
    parser.add_argument(
        "--topic", choices=list(TOPICS.keys()),
        help="Forcer un thème (sinon aléatoire)",
    )
    args = parser.parse_args()

    start = time.time()
    try:
        build_video(args.topic)
    except Exception as e:
        print(f"\n❌ Erreur : {e}", file=sys.stderr)
        import traceback; traceback.print_exc()
        return 1
    print(f"⏱️  Temps total : {time.time() - start:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
