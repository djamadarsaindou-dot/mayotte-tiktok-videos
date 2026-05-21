"""Script principal : génère une vidéo TikTok complète (2min+, voix masculine, multi-visuels)."""
import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from src.config import (
    COQUI_SPEAKER,
    FINAL_VIDEOS_DIR,
    OUTPUT_DIR,
    PEXELS_API_KEY,
    PIXABAY_API_KEY,
    POLLINATIONS_PARALLEL,
    TEMP_DIR,
    TTS_PROVIDER,
    VIDEO_HEIGHT,
    VIDEO_WIDTH,
    VISUAL_PROVIDER,
    VISUALS_PER_SCENE,
    VOICE,
)
from src.audio_master import master_voice
from src.editor import assemble_video, get_audio_duration
from src.script_writer import generate_script
from src.stock_finder import find_ai_asset, find_asset, find_stock_asset
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


GENERIC_FALLBACK_PROMPT = (
    "tropical island Indian Ocean turquoise lagoon palm trees aerial view, "
    "cinematic, vertical 9:16, photorealistic"
)

# Chronométrage par phase — sert à diagnostiquer les goulots d'étranglement
# (quelle phase prend le plus de temps : voix, visuels, montage, upload…).
_PHASE_TIMINGS: dict[str, float] = {}


@contextmanager
def _timed(label: str):
    """Mesure et logge la durée d'une phase du pipeline."""
    t0 = time.time()
    try:
        yield
    finally:
        dt = time.time() - t0
        _PHASE_TIMINGS[label] = _PHASE_TIMINGS.get(label, 0.0) + dt
        print(f"   ⏱️  [{label}] {dt:.0f}s")


def _print_timing_report() -> None:
    """Affiche le récap des durées par phase, trié du plus lent au plus rapide."""
    if not _PHASE_TIMINGS:
        return
    total = sum(_PHASE_TIMINGS.values())
    print("\n┌─ ⏱️  Répartition du temps ─────────────────────────")
    for label, dt in sorted(_PHASE_TIMINGS.items(), key=lambda x: -x[1]):
        pct = (dt / total * 100) if total else 0
        bar = "█" * int(pct / 4)
        print(f"│ {label:20s} {dt:6.0f}s  {pct:5.1f}%  {bar}")
    print(f"└─ total mesuré : {total:.0f}s")


def fetch_visual(args) -> tuple[int, int, Path, str, str]:
    """Pour la scène scene_idx, visuel visual_idx, télécharge l'asset.

    Mode HYBRIDE :
    - visual_idx == 0 : IA Pollinations (ancre du sens, corrélation forte texte/image)
    - visual_idx > 0  : stock (Pexels/Pixabay/Wikimedia) — rapide

    En cas d'échec total, retombe sur une requête Mayotte générique.
    """
    scene_idx, visual_idx, query, fallback_prompt, work_dir = args
    name = f"asset_s{scene_idx:02d}_v{visual_idx}"
    mayotte = _is_mayotte_specific(query) or _is_mayotte_specific(fallback_prompt)
    finder = find_ai_asset if visual_idx == 0 else find_stock_asset
    try:
        asset, source = finder(query, fallback_prompt, work_dir, name, mayotte_specific=mayotte)
        return scene_idx, visual_idx, asset, query, source
    except Exception as e:
        print(f"   ⚠️  Visuel s{scene_idx+1:02d}.v{visual_idx+1} a échoué ({str(e)[:60]}), fallback générique")
        try:
            asset, source = find_asset(
                "tropical island lagoon Mayotte aerial",
                GENERIC_FALLBACK_PROMPT,
                work_dir,
                f"{name}_fallback",
                mayotte_specific=True,
            )
            return scene_idx, visual_idx, asset, query, f"{source} (fallback générique)"
        except Exception as e2:
            print(f"   ❌ Fallback aussi échoué : {str(e2)[:80]}")
            raise


def build_video(topic_key: str | None = None) -> Path:
    if topic_key and topic_key in TOPICS:
        topic_def = TOPICS[topic_key]
    else:
        topic_key, topic_def = random_topic()

    print(f"\n🎬 Thème : {topic_def['label']}")
    print("📝 Génération du scénario via Groq (2 passes, peut prendre 1 min)...")
    with _timed("Script LLM"):
        script = generate_script(topic_def)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = slugify(script.get("title", topic_key))
    work_dir = TEMP_DIR / f"{timestamp}_{slug}"
    work_dir.mkdir(parents=True, exist_ok=True)

    # Texte avec ponctuation forte + sauts de ligne pour pauses naturelles
    full_text = assemble_narration([s["narration"] for s in script["scenes"]])
    audio_path = work_dir / "voice.mp3"

    print("🔊 Synthèse vocale...")
    with _timed("Voix (TTS)"):
        words = synthesize(full_text, audio_path)

    # Mastering : voix « radio » (highpass + EQ + compression + normalisation)
    print("   🎚️  Mastering audio de la voix...")
    try:
        with _timed("Mastering audio"):
            master_voice(audio_path)
    except Exception as e:
        print(f"   ⚠️  Mastering échoué ({str(e)[:60]}), voix brute conservée")

    audio_duration = get_audio_duration(audio_path)
    print(f"   Durée audio : {audio_duration:.1f}s | {len(words)} mots avec timing")

    ass_path = work_dir / "subs.ass"
    hook_punch = script.get("hook_punch", "")
    if hook_punch:
        print(f"   🎯 Hook visuel : « {hook_punch} »")
    build_karaoke_ass(words, ass_path, VIDEO_WIDTH, VIDEO_HEIGHT, hook_text=hook_punch)

    # Sauvegarde les timings des mots → permet de re-générer les sous-titres
    # plus tard (rerender) sans relancer la synthèse vocale.
    (work_dir / "words.json").write_text(
        json.dumps(words, ensure_ascii=False), encoding="utf-8"
    )

    print(f"🎨 Récup assets — MODE HYBRIDE (1 IA + {VISUALS_PER_SCENE-1} stock par scène)")
    print(f"   {len(script['scenes'])} scènes × {VISUALS_PER_SCENE} visuels = "
          f"{len(script['scenes']) * VISUALS_PER_SCENE} clips")

    # Construit la liste de tâches : (scene_idx, visual_idx, query, fallback, work_dir)
    all_tasks = []
    for s_idx, scene in enumerate(script["scenes"]):
        visuals = scene.get("visuals", [])
        while len(visuals) < VISUALS_PER_SCENE:
            visuals.append(scene.get("image_prompt", ""))
        for v_idx, query in enumerate(visuals[:VISUALS_PER_SCENE]):
            all_tasks.append((s_idx, v_idx, query, scene.get("image_prompt", ""), work_dir))

    # On sépare en 2 phases pour éviter que plusieurs IA se déclenchent en
    # parallèle (Pollinations rate-limit).
    ai_tasks = [t for t in all_tasks if t[1] == 0]       # visual_idx == 0 → IA
    stock_tasks = [t for t in all_tasks if t[1] != 0]    # autres → stock rapide

    visual_results: dict[tuple[int, int], Path] = {}
    sources_used: dict[str, int] = {}

    # Phase 1 : stock en parallèle (rapide) — les Pexels acceptent le parallélisme
    print(f"   🏃 Phase stock ({len(stock_tasks)} visuels, parallélisme {POLLINATIONS_PARALLEL})...")
    with _timed("Visuels stock"):
        with ThreadPoolExecutor(max_workers=max(1, POLLINATIONS_PARALLEL)) as ex:
            for s_idx, v_idx, asset, query, source in ex.map(fetch_visual, stock_tasks):
                visual_results[(s_idx, v_idx)] = asset
                sources_used[source] = sources_used.get(source, 0) + 1
                print(f"   ✓ s{s_idx+1:02d}.v{v_idx+1} [{source[:22]:22s}] {query[:42]}")

    # Phase 2 : IA en parallèle limité (2 simultanées) — équilibre vitesse/rate-limit
    AI_PARALLEL = 2
    print(f"   🎨 Phase IA ({len(ai_tasks)} visuels, parallélisme {AI_PARALLEL})...")
    with _timed("Visuels IA"):
        with ThreadPoolExecutor(max_workers=AI_PARALLEL) as ex:
            for s_idx, v_idx, asset, query, source in ex.map(fetch_visual, ai_tasks):
                visual_results[(s_idx, v_idx)] = asset
                sources_used[source] = sources_used.get(source, 0) + 1
                print(f"   ✓ s{s_idx+1:02d}.v{v_idx+1} [{source[:22]:22s}] {query[:42]}")

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
    with _timed("Montage FFmpeg"):
        assemble_video(asset_paths, asset_durations, audio_path, ass_path, output_path, work_dir)

    caption = script.get("caption", {})

    meta_path = OUTPUT_DIR / f"{timestamp}_{slug}.json"
    meta_path.write_text(
        json.dumps({
            "title": script.get("title"),
            "topic": topic_key,
            "topic_label": topic_def["label"],
            "hook": script.get("hook"),
            "hook_punch": script.get("hook_punch"),
            "caption": caption,
            "scenes": script["scenes"],
            "duration": audio_duration,
            "word_count": total_words,
            "num_clips": len(asset_paths),
            "sources_used": sources_used,
            "voice": f"Coqui XTTS v2 / {COQUI_SPEAKER}" if TTS_PROVIDER == "coqui" else f"Edge-TTS / {VOICE}",
            "created_at": datetime.now().isoformat(),
            "video_file": output_path.name,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Fichier .txt prêt à copier-coller au moment de publier sur TikTok
    caption_path = OUTPUT_DIR / f"{timestamp}_{slug}.txt"
    caption_text = caption.get("text") if isinstance(caption, dict) else None
    if caption_text:
        caption_path.write_text(
            f"{script.get('title', '')}\n\n{caption_text}\n",
            encoding="utf-8",
        )

    src_summary = ", ".join(f"{n}× {s}" for s, n in sorted(sources_used.items(), key=lambda x: -x[1]))
    print(f"\n✅ Vidéo prête : {output_path}")
    print(f"   Durée : {audio_duration:.0f}s | {total_words} mots | {len(asset_paths)} clips")
    print(f"   Sources : {src_summary}")

    # Copie la vidéo finale + métadonnées + légende dans le dossier dédié de l'utilisateur
    final_video = output_path
    try:
        import shutil
        FINAL_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
        final_video = FINAL_VIDEOS_DIR / output_path.name
        shutil.copy2(output_path, final_video)
        shutil.copy2(meta_path, FINAL_VIDEOS_DIR / meta_path.name)
        if caption_text and caption_path.exists():
            shutil.copy2(caption_path, FINAL_VIDEOS_DIR / caption_path.name)
        print(f"📂 Copie dans : {final_video}")
        if caption_text:
            print(f"📱 Légende TikTok : {caption_path.name}")
    except Exception as e:
        print(f"⚠️  Copie vers dossier final a échoué : {e}")

    # Notification Windows : « vidéo prête » avec bouton pour ouvrir le dossier
    try:
        from src.notify import notify_video_ready
        notify_video_ready(final_video, caption_text)
    except Exception as e:
        print(f"  ℹ️  Notification : {e}")

    # Auto-publication TikTok (mode brouillon — l'utilisateur valide dans l'app)
    try:
        from src.config import TIKTOK_AUTO_PUBLISH
        if TIKTOK_AUTO_PUBLISH:
            from src.tiktok_publisher import is_configured, publish_inbox
            if is_configured():
                with _timed("Upload TikTok"):
                    result = publish_inbox(final_video)
                # Push Telegram pour pouvoir valider depuis le téléphone
                try:
                    from src.telegram_notifier import is_configured as tg_ok, send_draft_ready
                    if tg_ok():
                        send_draft_ready(
                            video_name=final_video.name,
                            caption=caption_text or "",
                            publish_id=result.get("publish_id"),
                        )
                except Exception as e:
                    print(f"  ℹ️  Telegram : {e}")
            else:
                print("  ℹ️  TIKTOK_AUTO_PUBLISH=true mais tokens manquants. "
                      "Lance scripts/setup_tiktok.py.")
    except Exception as e:
        print(f"  ⚠️  Publication TikTok a échoué : {e}")
        # Notif Telegram d'erreur (best-effort)
        try:
            from src.telegram_notifier import send_error
            send_error(f"Publication TikTok : {e}")
        except Exception:
            pass

    _print_timing_report()
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Génère une vidéo TikTok automatiquement")
    parser.add_argument("--topic", choices=list(TOPICS.keys()), help="Forcer un thème")
    args = parser.parse_args()

    # Verrou mono-instance : si une génération tourne déjà, on s'arrête net
    # (évite tout doublon de génération → gaspillage d'API Mistral/Pollinations).
    from src.locking import acquire
    if not acquire(TEMP_DIR.parent.parent / "logs" / "generate.lock"):
        print("⚠️  Une génération est déjà en cours — ce doublon s'arrête.")
        return 0

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
