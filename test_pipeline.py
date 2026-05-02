"""Test du pipeline sans Groq : utilise un scénario codé en dur."""
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

from src.config import OUTPUT_DIR, TEMP_DIR, VIDEO_HEIGHT, VIDEO_WIDTH
from src.editor import assemble_video, get_audio_duration
from src.images import generate_image
from src.subtitles import srt_to_ass
from src.voice import synthesize


FAKE_SCRIPT = {
    "title": "Le double lagon de Mayotte",
    "hook": "Saviez-vous que Mayotte cache un trésor géologique unique au monde ?",
    "scenes": [
        {
            "narration": "Saviez-vous que Mayotte cache un trésor géologique unique au monde ?",
            "image_prompt": "aerial drone view of Mayotte tropical lagoon, turquoise water, coral reef, sunny day, cinematic",
        },
        {
            "narration": "Son lagon est l'un des rares doubles lagons fermés de la planète.",
            "image_prompt": "aerial view of double coral lagoon with two reef barriers, blue ocean, tropical island",
        },
        {
            "narration": "Une barrière de corail entoure une seconde barrière intérieure.",
            "image_prompt": "underwater coral reef barrier in clear blue water, tropical fish, sunlight rays",
        },
        {
            "narration": "Cette merveille abrite des centaines d'espèces marines protégées.",
            "image_prompt": "colorful tropical fish swimming around coral reef, sea turtle, vibrant underwater scene",
        },
        {
            "narration": "Mayotte est ainsi un véritable joyau de l'océan Indien.",
            "image_prompt": "sunset over Mayotte lagoon, palm trees silhouette, golden hour, peaceful tropical landscape",
        },
    ],
}


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return text[:50] or "video"


def main() -> int:
    script = FAKE_SCRIPT
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = slugify(script["title"])
    work_dir = TEMP_DIR / f"{timestamp}_{slug}"
    work_dir.mkdir(parents=True, exist_ok=True)

    full_text = " ".join(s["narration"].strip() for s in script["scenes"])
    audio_path = work_dir / "voice.mp3"
    srt_path = work_dir / "subs.srt"
    ass_path = work_dir / "subs.ass"

    print("🔊 Synthèse vocale (Edge-TTS)...")
    t0 = time.time()
    synthesize(full_text, audio_path, srt_path)
    audio_duration = get_audio_duration(audio_path)
    print(f"   Audio : {audio_duration:.1f}s en {time.time()-t0:.1f}s")

    srt_to_ass(srt_path, ass_path, VIDEO_WIDTH, VIDEO_HEIGHT)

    print(f"🎨 Génération de {len(script['scenes'])} images...")
    image_paths: list[Path] = []
    seed_base = random.randint(1, 1_000_000)
    for i, scene in enumerate(script["scenes"]):
        img_path = work_dir / f"scene_{i:02d}.jpg"
        prompt = scene["image_prompt"] + ", cinematic, vertical 9:16, no text"
        print(f"   [{i+1}/{len(script['scenes'])}] {scene['image_prompt'][:60]}...")
        t0 = time.time()
        generate_image(prompt, img_path, seed=seed_base + i)
        print(f"     OK en {time.time()-t0:.1f}s")
        image_paths.append(img_path)

    word_counts = [len(s["narration"].split()) for s in script["scenes"]]
    total_words = sum(word_counts) or 1
    scene_durations = [audio_duration * (w / total_words) for w in word_counts]

    output_path = OUTPUT_DIR / f"{timestamp}_{slug}.mp4"
    print("🎞️  Montage final...")
    t0 = time.time()
    assemble_video(image_paths, scene_durations, audio_path, ass_path, output_path)
    print(f"   Montage en {time.time()-t0:.1f}s")

    meta_path = OUTPUT_DIR / f"{timestamp}_{slug}.json"
    meta_path.write_text(
        json.dumps({
            "title": script["title"],
            "topic": "test",
            "topic_label": "Test pipeline",
            "hook": script.get("hook"),
            "scenes": script["scenes"],
            "duration": audio_duration,
            "created_at": datetime.now().isoformat(),
            "video_file": output_path.name,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\n✅ Vidéo prête : {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
