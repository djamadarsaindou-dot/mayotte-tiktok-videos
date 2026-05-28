"""Montage vidéo : assemble assets (images OU vidéos) + voix + sous-titres."""
import subprocess
from pathlib import Path

from src.config import (
    ASSETS_DIR,
    FFMPEG,
    VIDEO_FPS,
    VIDEO_HEIGHT,
    VIDEO_WIDTH,
    VISUALS_PER_SCENE,
)

FONTS_DIR = ASSETS_DIR / "fonts"
SFX_DIR = ASSETS_DIR / "sfx"


def _ffprobe_path() -> str:
    p = Path(FFMPEG)
    sibling = p.with_name(p.name.replace("ffmpeg", "ffprobe", 1))
    if sibling.exists():
        return str(sibling)
    return "ffprobe"


def _ffprobe_duration(path: Path) -> float:
    out = subprocess.check_output(
        [_ffprobe_path(), "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        text=True,
    )
    return float(out.strip())


def get_audio_duration(audio_path: Path) -> float:
    return _ffprobe_duration(audio_path)


def _is_video(path: Path) -> bool:
    return path.suffix.lower() in {".mp4", ".mov", ".webm", ".mkv"}


def _normalize_asset(asset_path: Path, target_path: Path, duration: float, scene_index: int) -> Path:
    """Convertit un asset (image OU vidéo) en clip vertical 1080x1920 de durée exacte.

    - Pour une image : Ken Burns (zoom progressif).
    - Pour une vidéo : crop+scale center, boucle si trop courte, troncature sinon.
    """
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Fondu d'entrée court sur les clips qui démarrent une nouvelle scène
    # (transition douce). Le tout 1er clip est exclu : il a déjà le flash
    # blanc d'intro géré au montage final.
    is_scene_start = scene_index % VISUALS_PER_SCENE == 0 and scene_index > 0
    fade_suffix = ",fade=t=in:st=0:d=0.22" if is_scene_start else ""

    if _is_video(asset_path):
        src_dur = _ffprobe_duration(asset_path)
        loops = 0
        if src_dur < duration:
            loops = int(duration // src_dur) + 1
        scale_filter = (
            f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},"
            f"setsar=1,fps={VIDEO_FPS}{fade_suffix}"
        )
        cmd = [FFMPEG, "-y"]
        if loops > 0:
            cmd += ["-stream_loop", str(loops)]
        cmd += [
            "-i", str(asset_path),
            "-an",
            "-t", f"{duration:.3f}",
            "-vf", scale_filter,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-r", str(VIDEO_FPS),
            str(target_path),
        ]
    else:
        # IMAGE : Ken Burns via zoompan.
        # Le bug classique de zoompan : il produit `d` frames PAR FRAME D'INPUT.
        # Solution : forcer 1 frame d'input (-frames:v 1 sur input, puis re-loop sur output).
        # Plus simple : `-loop 1 -i image -vf "...,zoompan=d=N:fps=FPS:s=WxH" -t DURATION`
        # avec -t en SORTIE pour limiter la durée finale.
        frames = max(1, int(duration * VIDEO_FPS))
        denom = max(1, frames - 1)
        # Ken Burns varié : 4 mouvements de caméra alternés pour éviter
        # l'effet répétitif (zoom avant / arrière / pano horizontal / vertical).
        mode = scene_index % 4
        if mode == 0:            # zoom avant, centré
            z = "min(zoom+0.0012,1.35)"
            x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
        elif mode == 1:          # zoom arrière, centré
            z = "if(lte(zoom,1.0),1.35,max(zoom-0.0012,1.05))"
            x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
        elif mode == 2:          # panoramique gauche → droite, zoom fixe
            z = "1.2"
            x, y = f"(iw-iw/zoom)*on/{denom}", "ih/2-(ih/zoom/2)"
        else:                    # panoramique haut → bas, zoom fixe
            z = "1.2"
            x, y = "iw/2-(iw/zoom/2)", f"(ih-ih/zoom)*on/{denom}"
        kb = (
            f"scale={VIDEO_WIDTH*2}:{VIDEO_HEIGHT*2}:force_original_aspect_ratio=increase,"
            f"crop={VIDEO_WIDTH*2}:{VIDEO_HEIGHT*2},"
            f"zoompan=z='{z}':x='{x}':y='{y}':"
            f"d={frames}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={VIDEO_FPS},setsar=1,"
            f"trim=duration={duration:.3f}{fade_suffix}"
        )
        cmd = [
            FFMPEG, "-y",
            "-loop", "1",
            "-framerate", "1",       # 1 input frame/sec → zoompan ne multiplie pas
            "-i", str(asset_path),
            "-vf", kb,
            "-t", f"{duration:.3f}",  # filet de sécurité côté sortie
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-r", str(VIDEO_FPS),
            str(target_path),
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr[-1500:])
        raise RuntimeError(f"FFmpeg normalize a échoué (asset={asset_path.name})")
    return target_path


def _mix_sfx(audio_path: Path, scene_durations: list[float], work_dir: Path) -> Path:
    """Mixe la voix avec un impact d'intro et un whoosh à chaque transition
    de scène. Retourne le chemin de l'audio mixé, ou l'audio original si les
    SFX sont absents ou si le mix échoue (dégradation gracieuse).

    Le sound design léger rend les transitions audibles et donne un effet
    « production pro » sans masquer la voix.
    """
    whoosh = SFX_DIR / "whoosh.wav"
    impact = SFX_DIR / "impact.wav"
    if not whoosh.exists() or not impact.exists():
        return audio_path

    # Positions cumulées des transitions de scène (fin de chaque groupe de
    # VISUALS_PER_SCENE clips), sauf la toute dernière (= fin de vidéo).
    cum = 0.0
    transitions: list[float] = []
    for i, d in enumerate(scene_durations):
        cum += d
        if (i + 1) % VISUALS_PER_SCENE == 0 and i < len(scene_durations) - 1:
            transitions.append(cum)

    mixed = work_dir / "voice_mixed.m4a"
    inputs = ["-i", str(audio_path), "-i", str(impact)]
    for _ in transitions:
        inputs += ["-i", str(whoosh)]

    # Impact d'intro à 220 ms (juste après le début), volume modéré pour ne
    # pas couvrir la voix. Whooshes 80 ms avant chaque transition pour donner
    # l'impression d'anticiper la coupe.
    parts = ["[1:a]adelay=220|220,volume=0.45[hookimp]"]
    for j, pos in enumerate(transitions):
        delay_ms = max(0, int(pos * 1000) - 80)
        parts.append(f"[{j+2}:a]adelay={delay_ms}|{delay_ms},volume=0.40[w{j}]")
    streams = "[0:a][hookimp]" + "".join(f"[w{j}]" for j in range(len(transitions)))
    n = 2 + len(transitions)
    parts.append(
        f"{streams}amix=inputs={n}:duration=first:dropout_transition=0,"
        f"volume=1.1[out]"
    )

    cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error"] + inputs + [
        "-filter_complex", ";".join(parts),
        "-map", "[out]",
        "-c:a", "aac", "-b:a", "192k",
        str(mixed),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ⚠️  Sound design : mix échoué, voix brute conservée")
        return audio_path
    print(f"  🔊 Sound design : impact intro + {len(transitions)} whooshes")
    return mixed


def assemble_video(
    asset_paths: list[Path],
    scene_durations: list[float],
    audio_path: Path,
    ass_path: Path,
    output_path: Path,
    work_dir: Path,
) -> Path:
    if len(asset_paths) != len(scene_durations):
        raise ValueError("asset_paths et scene_durations doivent avoir la même longueur")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    clips_dir = work_dir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    print(f"  ▶ Normalisation des {len(asset_paths)} clips...")
    normalized: list[Path] = []
    for i, (asset, dur) in enumerate(zip(asset_paths, scene_durations)):
        clip = clips_dir / f"clip_{i:02d}.mp4"
        _normalize_asset(asset, clip, dur, i)
        normalized.append(clip)

    concat_list = clips_dir / "concat.txt"
    concat_list.write_text(
        "\n".join(f"file '{p.resolve().as_posix()}'" for p in normalized),
        encoding="utf-8",
    )

    silent_concat = clips_dir / "concat.mp4"
    cmd = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c", "copy",
        str(silent_concat),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr[-1500:])
        raise RuntimeError("FFmpeg concat a échoué")

    audio_dur = _ffprobe_duration(audio_path)

    # === Sound design : mixe la voix avec un impact d'intro + whooshes ===
    # à chaque transition de scène. Si les SFX sont absents, on garde la voix
    # brute (dégradation gracieuse).
    mixed_audio = _mix_sfx(audio_path, scene_durations, work_dir)

    ass_escaped = str(ass_path.resolve()).replace("\\", "/").replace(":", "\\:")
    fonts_escaped = str(FONTS_DIR.resolve()).replace("\\", "/").replace(":", "\\:")

    # Barre de progression : un rectangle cyan qui se remplit de gauche à droite
    # sur toute la durée. La largeur dépend du temps courant `t`.
    bar_h = 12
    bar_filter = (
        f"drawbox=x=0:y=ih-{bar_h}:"
        f"w='iw*min(t/{audio_dur:.3f}\\,1)':h={bar_h}:"
        f"color=0x00F0FF@0.92:t=fill"
    )

    # === Hook visuel des 3 premières secondes ===
    # 1. Flash blanc en intro (fade-in from white sur 0.3s) — pattern interrupt
    #    qui stoppe le scroll TikTok dès les premières frames.
    # 2. Zoom out subtil 110% → 100% sur 2s — effet cinéma qui happe le regard.
    hook_zoom = (
        f"scale='iw*(1.10-0.05*min(t\\,2))':'ih*(1.10-0.05*min(t\\,2))':eval=frame,"
        f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},"
    )
    hook_intro_fade = "fade=t=in:st=0:d=0.3:color=white,"

    # === Color grading cinéma ===
    # Harmonise les images de sources variées (Pexels, Cloudflare IA, Pixabay)
    # en un look tropical chaud et contrasté, type documentaire. Appliqué AVANT
    # l'ass pour ne pas altérer les couleurs des sous-titres/emojis.
    grade_filter = (
        "eq=contrast=1.08:saturation=1.20:brightness=0.01:gamma=0.98,"
        "colorbalance=rs=0.03:gm=0.01:bs=-0.04"
    )

    # Branding : le watermark « @mister_decouverte » est dessiné par le
    # système ASS (voir Style "Brand" dans subtitles.py) — plus fiable sur
    # Windows que drawtext FFmpeg qui dépend de fontconfig.
    vf = (
        f"{grade_filter},{hook_zoom}{hook_intro_fade}{bar_filter},"
        f"ass='{ass_escaped}':fontsdir='{fonts_escaped}'"
    )

    cmd = [
        FFMPEG, "-y",
        "-i", str(silent_concat),
        "-i", str(mixed_audio),
        "-vf", vf,
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-r", str(VIDEO_FPS),
        "-shortest",
        "-movflags", "+faststart",
        str(output_path),
    ]

    print(f"  ▶ Encodage final + sous-titres...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr[-2000:])
        raise RuntimeError(f"FFmpeg final a échoué (code {result.returncode})")

    return output_path
