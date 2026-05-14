"""Montage vidéo : assemble assets (images OU vidéos) + voix + sous-titres."""
import subprocess
from pathlib import Path

from src.config import ASSETS_DIR, FFMPEG, VIDEO_FPS, VIDEO_HEIGHT, VIDEO_WIDTH

FONTS_DIR = ASSETS_DIR / "fonts"


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

    if _is_video(asset_path):
        src_dur = _ffprobe_duration(asset_path)
        loops = 0
        if src_dur < duration:
            loops = int(duration // src_dur) + 1
        scale_filter = (
            f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},"
            f"setsar=1,fps={VIDEO_FPS}"
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
        if scene_index % 2 == 0:
            zoom_expr = "min(zoom+0.0012,1.35)"
        else:
            zoom_expr = "if(lte(zoom,1.0),1.35,max(zoom-0.0012,1.05))"
        kb = (
            f"scale={VIDEO_WIDTH*2}:{VIDEO_HEIGHT*2}:force_original_aspect_ratio=increase,"
            f"crop={VIDEO_WIDTH*2}:{VIDEO_HEIGHT*2},"
            f"zoompan=z='{zoom_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={VIDEO_FPS},setsar=1,"
            f"trim=duration={duration:.3f}"
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

    ass_escaped = str(ass_path.resolve()).replace("\\", "/").replace(":", "\\:")
    fonts_escaped = str(FONTS_DIR.resolve()).replace("\\", "/").replace(":", "\\:")
    cmd = [
        FFMPEG, "-y",
        "-i", str(silent_concat),
        "-i", str(audio_path),
        "-vf", f"ass='{ass_escaped}':fontsdir='{fonts_escaped}'",
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
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
