"""Script principal : génère une vidéo TikTok complète (2min+, voix masculine, multi-visuels)."""
import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from src.config import (
    OUTPUT_DIR,
    PEXELS_API_KEY,
    PIXABAY_API_KEY,
    TEMP_DIR,
    VIDEO_HEIGHT,
    VIDEO_WIDTH,
    VISUALS_PER_SCENE,
)
from src.editor import assemble_video, get_audio_duration
from src.script_writer import generate_script
from src.stock_finder import find_asset
from src.subtitles import build_karaoke_ass
from src.topics import TOPICS, random_topic
from src.voice import assemble_narration, synthesize


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return text[:50] or "video"


MAYOTTE_KEYWORDS_RE = re.compile(
    r"\b(mayotte|choungui|mahor[aé]is?|mamoudzou|petite[\s-]terre|grande[\s-]terre|"
    r"ylang|dziani|ngouja|combani|sazile|pamandzi|maki|debaa|chigoma|m[\W_]?biwi|"
    r"manzaraka|salouva|msindzano|djarifa|banga|kashkasi|kusi|dugong|trimba|saziley)\b",
    re.IGNORECASE,
)


def _is_mayotte_specific(query: str) -> bool:
    return bool(MAYOTTE_KEYWORDS_RE.search(query))


def fetch_visual(args) -> tuple[int, int, Path, str, str]:
    """Pour la scène scene_idx, visuel visual_idx, télécharge l'asset."""
    scene_idx, visual_idx, query, fallback_prompt, work_dir = args
    name = f"asset_s{scene_idx:02d}_v{visual_idx}"
    mayotte = _is_mayotte_specific(query) or _is_mayotte_specific(fallback_prompt)
    asset, source = find_asset(query, fallback_prompt, work_dir, name, mayotte_specific=mayotte)
    return scene_idx, visual_idx, asset, query, source


def build_video(topic_key: str | None = None) -> Path:
    if topic_key and topic_key in TOPICS:
        topic_def = TOPICS[topic_key]
    else:
        topic_key, topic_def = random_topic()

    print(f"\n🎬 Thème : {topic_def['label']}")
    print("📝 Génération du scénario via Groq (2 passes, peut prendre 1 min)...")
    script = generate_script(topic_def)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = slugify(script.get("title", topic_key))
    work_dir = TEMP_DIR / f"{timestamp}_{slug}"
    work_dir.mkdir(parents=True, exist_ok=True)

    # Texte avec ponctuation forte + sauts de ligne pour pauses naturelles
    full_text = assemble_narration([s["narration"] for s in script["scenes"]])
    audio_path = work_dir / "voice.mp3"

    print("🔊 Synthèse vocale (Edge-TTS, voix Henri)...")
    words = synthesize(full_text, audio_path)
    audio_duration = get_audio_duration(audio_path)
    print(f"   Durée audio : {audio_duration:.1f}s | {len(words)} mots avec timing")

    ass_path = work_dir / "subs.ass"
    build_karaoke_ass(words, ass_path, VIDEO_WIDTH, VIDEO_HEIGHT)

    sources = []
    if PEXELS_API_KEY: sources.append("Pexels")
    if PIXABAY_API_KEY: sources.append("Pixabay")
    sources.append("Pollinations IA")
    print(f"🎨 Récup assets ({' → '.join(sources)})...")
    print(f"   {len(script['scenes'])} scènes × {VISUALS_PER_SCENE} visuels = "
          f"{len(script['scenes']) * VISUALS_PER_SCENE} clips")

    # Construit la liste de tâches : (scene_idx, visual_idx, query, fallback, work_dir)
    tasks = []
    for s_idx, scene in enumerate(script["scenes"]):
        visuals = scene.get("visuals", [])
        while len(visuals) < VISUALS_PER_SCENE:
            visuals.append(scene.get("image_prompt", ""))
        for v_idx, query in enumerate(visuals[:VISUALS_PER_SCENE]):
            tasks.append((s_idx, v_idx, query, scene.get("image_prompt", ""), work_dir))

    # Recherche parallèle (4 workers, sources externes acceptent ce parallélisme)
    visual_results: dict[tuple[int, int], Path] = {}
    sources_used: dict[str, int] = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        for s_idx, v_idx, asset, query, source in ex.map(fetch_visual, tasks):
            visual_results[(s_idx, v_idx)] = asset
            sources_used[source] = sources_used.get(source, 0) + 1
            print(f"   ✓ s{s_idx+1:02d}.v{v_idx+1} [{source[:18]:18s}] {query[:45]}")

    # Calcul des durées : chaque scène consomme une fraction de l'audio
    # proportionnelle à son nombre de mots, puis on divise entre ses 3 visuels
    word_counts = [len(s["narration"].split()) for s in script["scenes"]]
    total_words = sum(word_counts) or 1
    asset_paths: list[Path] = []
    asset_durations: list[float] = []
    for s_idx, scene in enumerate(script["scenes"]):
        scene_dur = audio_duration * (word_counts[s_idx] / total_words)
        per_visual = scene_dur / VISUALS_PER_SCENE
        for v_idx in range(VISUALS_PER_SCENE):
            asset_paths.append(visual_results[(s_idx, v_idx)])
            asset_durations.append(per_visual)

    output_path = OUTPUT_DIR / f"{timestamp}_{slug}.mp4"
    print(f"🎞️  Montage final ({len(asset_paths)} clips, durée moy {sum(asset_durations)/len(asset_durations):.1f}s)...")
    assemble_video(asset_paths, asset_durations, audio_path, ass_path, output_path, work_dir)

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
            "num_clips": len(asset_paths),
            "sources_used": sources_used,
            "voice": "fr-FR-HenriNeural",
            "created_at": datetime.now().isoformat(),
            "video_file": output_path.name,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    src_summary = ", ".join(f"{n}× {s}" for s, n in sorted(sources_used.items(), key=lambda x: -x[1]))
    print(f"\n✅ Vidéo prête : {output_path}")
    print(f"   Durée : {audio_duration:.0f}s | {total_words} mots | {len(asset_paths)} clips")
    print(f"   Sources : {src_summary}")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Génère une vidéo TikTok automatiquement")
    parser.add_argument("--topic", choices=list(TOPICS.keys()), help="Forcer un thème")
    args = parser.parse_args()

    start = time.time()
    try:
        build_video(args.topic)
    except Exception as e:
        print(f"\n❌ Erreur : {e}", file=sys.stderr)
        import traceback; traceback.print_exc()
        return 1
    print(f"⏱️  Temps total : {time.time() - start:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
