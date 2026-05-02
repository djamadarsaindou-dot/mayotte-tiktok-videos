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

from src.config import OUTPUT_DIR, TEMP_DIR
from src.editor import assemble_video, get_audio_duration
from src.images import generate_image
from src.script_writer import generate_script
from src.subtitles import srt_to_ass
from src.topics import TOPICS, random_topic
from src.voice import synthesize


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return text[:50] or "video"


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
    srt_path = work_dir / "subs.srt"
    ass_path = work_dir / "subs.ass"

    print("🔊 Synthèse vocale (Edge-TTS)...")
    synthesize(full_text, audio_path, srt_path)
    audio_duration = get_audio_duration(audio_path)
    print(f"   Durée audio : {audio_duration:.1f}s")

    from src.config import VIDEO_HEIGHT, VIDEO_WIDTH
    srt_to_ass(srt_path, ass_path, VIDEO_WIDTH, VIDEO_HEIGHT)

    print(f"🎨 Génération de {len(script['scenes'])} images via Pollinations (parallèle)...")
    seed_base = random.randint(1, 1_000_000)

    def _gen(i: int, scene: dict) -> tuple[int, Path]:
        img_path = work_dir / f"scene_{i:02d}.jpg"
        prompt = scene["image_prompt"] + ", cinematic, vertical 9:16, no text"
        generate_image(prompt, img_path, seed=seed_base + i)
        print(f"   ✓ [{i+1}/{len(script['scenes'])}] {scene['image_prompt'][:55]}...")
        return i, img_path

    image_paths: list[Path] = []
    for i, scene in enumerate(script["scenes"]):
        _, p = _gen(i, scene)
        image_paths.append(p)

    word_counts = [len(s["narration"].split()) for s in script["scenes"]]
    total_words = sum(word_counts) or 1
    scene_durations = [audio_duration * (w / total_words) for w in word_counts]

    output_path = OUTPUT_DIR / f"{timestamp}_{slug}.mp4"
    print("🎞️  Montage final...")
    assemble_video(image_paths, scene_durations, audio_path, ass_path, output_path)

    meta_path = OUTPUT_DIR / f"{timestamp}_{slug}.json"
    meta_path.write_text(
        json.dumps({
            "title": script.get("title"),
            "topic": topic_key,
            "topic_label": topic_def["label"],
            "hook": script.get("hook"),
            "scenes": script["scenes"],
            "duration": audio_duration,
            "created_at": datetime.now().isoformat(),
            "video_file": output_path.name,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\n✅ Vidéo prête : {output_path}")
    print(f"   Durée : {audio_duration:.1f}s")
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
        return 1
    print(f"⏱️  Temps total : {time.time() - start:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
