"""Montage vidéo : assemble images + voix + sous-titres avec FFmpeg."""
import subprocess
from pathlib import Path

from src.config import FFMPEG, VIDEO_FPS, VIDEO_HEIGHT, VIDEO_WIDTH


def _ffprobe_path() -> str:
    p = Path(FFMPEG)
    sibling = p.with_name(p.name.replace("ffmpeg", "ffprobe", 1))
    if sibling.exists():
        return str(sibling)
    return "ffprobe"


def _ffprobe_duration(audio_path: Path) -> float:
    out = subprocess.check_output(
        [_ffprobe_path(), "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
        text=True,
    )
    return float(out.strip())


def _ken_burns_filter(image_path: Path, duration: float, scene_index: int) -> str:
    """Effet zoom progressif (Ken Burns) sur une image fixe."""
    frames = max(1, int(duration * VIDEO_FPS))
    if scene_index % 2 == 0:
        zoom_expr = f"min(zoom+0.0015,1.4)"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"
    else:
        zoom_expr = f"if(lte(zoom,1.0),1.4,max(zoom-0.0015,1.05))"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"
    return (
        f"scale={VIDEO_WIDTH*2}:{VIDEO_HEIGHT*2}:force_original_aspect_ratio=increase,"
        f"crop={VIDEO_WIDTH*2}:{VIDEO_HEIGHT*2},"
        f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}':d={frames}:"
        f"s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={VIDEO_FPS}"
    )


def assemble_video(
    image_paths: list[Path],
    scene_durations: list[float],
    audio_path: Path,
    ass_path: Path,
    output_path: Path,
) -> Path:
    if len(image_paths) != len(scene_durations):
        raise ValueError("image_paths et scene_durations doivent avoir la même longueur")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    inputs: list[str] = []
    for img in image_paths:
        inputs += ["-loop", "1", "-i", str(img)]
    inputs += ["-i", str(audio_path)]

    filter_parts = []
    for i, dur in enumerate(scene_durations):
        kb = _ken_burns_filter(image_paths[i], dur, i)
        filter_parts.append(f"[{i}:v]{kb},trim=duration={dur:.3f},setpts=PTS-STARTPTS[v{i}]")

    concat_inputs = "".join(f"[v{i}]" for i in range(len(image_paths)))
    filter_parts.append(
        f"{concat_inputs}concat=n={len(image_paths)}:v=1:a=0,format=yuv420p[vraw]"
    )
    ass_escaped = str(ass_path.resolve()).replace("\\", "/").replace(":", "\\:")
    filter_parts.append(f"[vraw]ass='{ass_escaped}'[vout]")

    filter_complex = ";".join(filter_parts)
    audio_index = len(image_paths)

    cmd = [
        FFMPEG, "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", f"{audio_index}:a",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-r", str(VIDEO_FPS),
        "-shortest",
        "-movflags", "+faststart",
        str(output_path),
    ]

    print(f"  ▶️  FFmpeg encodage en cours...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr[-2000:])
        raise RuntimeError(f"FFmpeg a échoué (code {result.returncode})")

    return output_path


def get_audio_duration(audio_path: Path) -> float:
    return _ffprobe_duration(audio_path)
