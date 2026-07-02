"""Montage vidéo : assemble assets (images OU vidéos) + voix + sous-titres."""
import json
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
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
            "-c:v", "libx264", "-preset", "fast", "-crf", "17",
            "-pix_fmt", "yuv420p",
            "-r", str(VIDEO_FPS),
            str(target_path),
        ]
    else:
        # IMAGE : Ken Burns via zoompan, version anti-tremblement.
        # zoompan arrondit x/y au pixel ENTIER de la source → à taille native
        # le cadre saute d'un pixel de sortie à chaque frame (jitter visible).
        # Antidote : sur-échantillonner la source 4x AVANT zoompan — l'erreur
        # d'arrondi tombe à 1/4 de pixel de sortie, le mouvement devient fluide.
        # Une image = UNE frame d'input (pas de -loop) : zoompan génère ses
        # `d` frames tout seul, plus d'effet dent de scie au raccord.
        frames = max(2, int(duration * VIDEO_FPS))
        denom = max(1, frames - 1)
        inc = 0.0007  # zoom lent (≈2%/s) : un Ken Burns discret fait plus cinéma
        # Ken Burns varié : 4 mouvements de caméra alternés pour éviter
        # l'effet répétitif (zoom avant / arrière / pano horizontal / vertical).
        mode = scene_index % 4
        if mode == 0:            # zoom avant, centré
            z = f"min(1.0+{inc}*on,1.15)"
            x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
        elif mode == 1:          # zoom arrière, centré
            z = f"max(1.12-{inc}*on,1.0)"
            x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
        elif mode == 2:          # panoramique gauche → droite, zoom fixe
            z = "1.10"
            x, y = f"(iw-iw/zoom)*on/{denom}", "ih/2-(ih/zoom/2)"
        else:                    # panoramique haut → bas, zoom fixe
            z = "1.10"
            x, y = "iw/2-(iw/zoom/2)", f"(ih-ih/zoom)*on/{denom}"
        ss_w, ss_h = VIDEO_WIDTH * 4, VIDEO_HEIGHT * 4
        kb = (
            f"scale={ss_w}:{ss_h}:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop={ss_w}:{ss_h},"
            f"zoompan=z='{z}':x='{x}':y='{y}':"
            f"d={frames}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={VIDEO_FPS},setsar=1"
            f"{fade_suffix}"
        )
        cmd = [
            FFMPEG, "-y",
            "-i", str(asset_path),
            "-vf", kb,
            "-frames:v", str(frames),
            "-c:v", "libx264", "-preset", "fast", "-crf", "17",
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

    # Impact d'intro à 220 ms (juste après le début). Whooshes 80 ms avant
    # chaque transition pour donner l'impression d'anticiper la coupe.
    # Les SFX sont regroupés sur un bus [sfx] puis DUCKÉS sous la voix par
    # compression sidechain (clé = voix) : ils restent audibles entre les
    # phrases mais s'effacent dès que la voix parle — mix « production pro »
    # sans le boost aveugle volume=1.1 qui pouvait clipper.
    parts = ["[1:a]adelay=220|220,volume=0.5[hookimp]"]
    for j, pos in enumerate(transitions):
        delay_ms = max(0, int(pos * 1000) - 80)
        parts.append(f"[{j+2}:a]adelay={delay_ms}|{delay_ms},volume=0.45[w{j}]")
    if transitions:
        sfx_streams = "[hookimp]" + "".join(f"[w{j}]" for j in range(len(transitions)))
        parts.append(
            f"{sfx_streams}amix=inputs={1 + len(transitions)}:"
            f"duration=longest:normalize=0[sfx]"
        )
    else:
        parts.append("[hookimp]anull[sfx]")
    parts.append(
        "[sfx][0:a]sidechaincompress="
        "threshold=0.05:ratio=3:attack=20:release=250:makeup=1[duck]"
    )
    parts.append("[0:a][duck]amix=inputs=2:duration=first:normalize=0[out]")

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
    print(f"  🔊 Sound design : impact intro + {len(transitions)} whooshes (duckés)")
    return mixed


def _master_final_audio(audio_path: Path, work_dir: Path) -> Path:
    """Loudnorm 2 passes vers la cible TikTok (-14 LUFS, true peak -1.5 dB)
    sur le mix COMPLET voix+SFX — mesurer puis corriger en linéaire préserve
    la dynamique (le mode 1 passe pompe). Sortie AAC 48 kHz prête pour un
    mux en -c:a copy. En cas de pépin : simple transcodage AAC (jamais bloquant)."""
    out = work_dir / "audio_final.m4a"
    measure = subprocess.run(
        [FFMPEG, "-hide_banner", "-i", str(audio_path), "-af",
         "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    af = "loudnorm=I=-14:TP=-1.5:LRA=11"
    m = re.search(r'\{[^{}]*"input_i"[^{}]*\}', measure.stderr, re.S)
    if m:
        try:
            j = json.loads(m.group(0))
            af += (f":measured_I={j['input_i']}:measured_TP={j['input_tp']}"
                   f":measured_LRA={j['input_lra']}"
                   f":measured_thresh={j['input_thresh']}"
                   f":offset={j['target_offset']}:linear=true")
            print(f"  🎚️  Loudnorm 2 passes : {j['input_i']} LUFS → -14 LUFS")
        except (ValueError, KeyError):
            print("  ⚠️  Loudnorm : mesure illisible, normalisation 1 passe")
    else:
        print("  ⚠️  Loudnorm : mesure absente, normalisation 1 passe")
    result = subprocess.run(
        [FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
         "-i", str(audio_path), "-af", af,
         "-ar", "48000", "-c:a", "aac", "-b:a", "192k", str(out)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        # Toujours produire de l'AAC : le mux final fait -c:a copy.
        result = subprocess.run(
            [FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
             "-i", str(audio_path),
             "-ar", "48000", "-c:a", "aac", "-b:a", "192k", str(out)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError("FFmpeg : transcodage audio final a échoué")
    return out


def assemble_video(
    asset_paths: list[Path],
    scene_durations: list[float],
    audio_path: Path,
    ass_path: Path,
    output_path: Path,
    work_dir: Path,
    punch_times: list[float] | None = None,
) -> Path:
    """Assemble le montage final.

    punch_times : timestamps (secondes) des « punch-in » — micro-zooms secs
    de 0.18 s posés sur les moments forts (mots-clés). None ou liste vide =
    comportement historique, aucun filtre ajouté (rétro-compatible).
    """
    if len(asset_paths) != len(scene_durations):
        raise ValueError("asset_paths et scene_durations doivent avoir la même longueur")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    clips_dir = work_dir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    # Normalisation en PARALLÈLE : chaque clip = un subprocess FFmpeg (pas de
    # GIL en jeu), un encode x264 preset fast n'occupe que quelques threads →
    # 4 encodes simultanés saturent bien un CPU 14 cœurs sans étouffer la
    # machine. Réglable via NORMALIZE_WORKERS dans .env.
    workers = int(os.getenv("NORMALIZE_WORKERS", "4"))
    print(f"  ▶ Normalisation des {len(asset_paths)} clips ({workers} en parallèle)...")

    def _normalize_job(job: tuple[int, Path, float]) -> Path:
        i, asset, dur = job
        return _normalize_asset(asset, clips_dir / f"clip_{i:02d}.mp4", dur, i)

    jobs = list(zip(range(len(asset_paths)), asset_paths, scene_durations))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        # executor.map restitue les résultats DANS L'ORDRE de soumission :
        # l'ordre des clips (= le déroulé de la vidéo) est préservé. Si un
        # clip échoue, sa RuntimeError (avec le nom de l'asset fautif) remonte
        # ici ; l'itérateur de map annule les tâches pas encore lancées et le
        # `with` attend la fin des encodes déjà en cours (annulation propre).
        normalized: list[Path] = list(executor.map(_normalize_job, jobs))

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
    # brute (dégradation gracieuse). Puis mastering final : loudnorm 2 passes
    # vers -14 LUFS sur le mix complet (cible TikTok).
    mixed_audio = _mix_sfx(audio_path, scene_durations, work_dir)
    final_audio = _master_final_audio(mixed_audio, work_dir)

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
    # 2. Zoom out vif 110% → 100% sur 1.2s — intro plus nerveuse (rétention),
    #    0.0833 ≈ 0.10/1.2 : on atteint exactement 100% à t=1.2s.
    # PIÈGE crop : son x/y par défaut ((in_w-out_w)/2) est figé à l'init du
    # graphe — quand scale change la taille des frames EN COURS de flux, le
    # crop ne se recentre pas (zoom ancré en haut-gauche puis clampé à droite,
    # vérifié sur frames). Antidote : x/y EXPLICITES recalculés à chaque frame
    # via t (crop ré-évalue x/y par frame), centrés sur la taille zoomée.
    zoom_expr = "(1.10-0.0833*min(t\\,1.2))"
    hook_zoom = (
        f"scale='iw*{zoom_expr}':'ih*{zoom_expr}':eval=frame,"
        f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT}:"
        f"x='{VIDEO_WIDTH}*({zoom_expr}-1)/2':y='{VIDEO_HEIGHT}*({zoom_expr}-1)/2',"
    )
    hook_intro_fade = "fade=t=in:st=0:d=0.3:color=white,"

    # === Punch-in : micro-zoom sec sur les moments forts ===
    # Zoom de PUNCH_SCALE (7 % par défaut, surchargeable via .env) pendant
    # 0.18 s à chaque timestamp fourni : between(t, tk, tk+0.18) vaut 1
    # pendant le punch, 0 sinon. Les punchs ne se chevauchent jamais
    # (min_gap 2.5 s garanti en amont) → la somme des between() reste 0/1.
    # trunc(…/2)*2 force des dimensions paires (exigence yuv420p). Le crop
    # ramène au cadre 1080x1920 avec un x/y EXPLICITE recalculé à chaque
    # frame (même piège que hook_zoom : le x/y par défaut du crop est figé à
    # l'init → zoom ancré en haut-gauche au lieu du centre). Position dans la
    # chaîne : APRÈS le grading (couleurs stables) mais AVANT bar_filter et
    # ass — ni la barre de progression ni les sous-titres ne doivent zoomer.
    # Plafond : 12 punchs max (limite de longueur de ligne de commande Windows).
    punch_filter = ""
    if punch_times:
        punch_scale = float(os.getenv("PUNCH_SCALE", "0.07"))
        terms = "+".join(
            f"between(t\\,{tk:.3f}\\,{tk + 0.18:.3f})" for tk in punch_times[:12]
        )
        punch_expr = f"(1+{punch_scale:g}*({terms}))"
        punch_filter = (
            f"scale=w='trunc(iw*{punch_expr}/2)*2':h='trunc(ih*{punch_expr}/2)*2':eval=frame,"
            f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT}:"
            f"x='{VIDEO_WIDTH}*({punch_expr}-1)/2':y='{VIDEO_HEIGHT}*({punch_expr}-1)/2',"
        )

    # === Color grading cinéma ===
    # Harmonise les images de sources variées (Pexels, Cloudflare IA, Pixabay)
    # en un look tropical chaud et contrasté, type documentaire. Appliqué AVANT
    # l'ass pour ne pas altérer les couleurs des sous-titres/emojis.
    # L'identité visuelle de la chaîne = UNE LUT .cube fixe (générée par
    # scripts/make_luts.py) + vignette légère. Fallback sur l'ancien étalonnage
    # eq/colorbalance si la LUT manque (dégradation gracieuse).
    lut_path = ASSETS_DIR / "luts" / "mayotte_signature.cube"
    if lut_path.exists():
        lut_escaped = str(lut_path.resolve()).replace("\\", "/").replace(":", "\\:")
        grade_filter = (
            "eq=contrast=1.04:saturation=1.05,"
            f"lut3d=file='{lut_escaped}':interp=tetrahedral,"
            "vignette=angle=PI/5"
        )
    else:
        grade_filter = (
            "eq=contrast=1.08:saturation=1.20:brightness=0.01:gamma=0.98,"
            "colorbalance=rs=0.03:gm=0.01:bs=-0.04"
        )

    # Branding : le watermark « @mister_decouverte » est dessiné par le
    # système ASS (voir Style "Brand" dans subtitles.py) — plus fiable sur
    # Windows que drawtext FFmpeg qui dépend de fontconfig.
    # Grain temporel léger (pellicule) appliqué APRÈS le grading mais AVANT
    # les sous-titres : le texte reste parfaitement net. TikTok recompresse
    # fort → grain subtil uniquement (c0s>8 serait écrasé en bouillie).
    grain_filter = "noise=c0s=7:c0f=t+u"
    # Ordre impératif : grade → punch → hook_zoom → fade → bar → grain → ass
    # (le punch-in zoome l'image seule ; barre et sous-titres restent fixes).
    vf = (
        f"{grade_filter},{punch_filter}{hook_zoom}{hook_intro_fade}{bar_filter},{grain_filter},"
        f"ass='{ass_escaped}':fontsdir='{fonts_escaped}'"
    )

    # Encodage final pensé pour la RECOMPRESSION TikTok : la plateforme
    # ré-encode tout, la qualité de la source est la seule variable qu'on
    # contrôle. CRF 18 + preset slow + tags bt709 explicites (évite les
    # dérives couleur post-LUT). L'audio est déjà masterisé en AAC → copy.
    cmd = [
        FFMPEG, "-y",
        "-i", str(silent_concat),
        "-i", str(final_audio),
        "-vf", vf,
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-profile:v", "high", "-level", "4.1",
        "-pix_fmt", "yuv420p",
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-c:a", "copy",
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


def make_cover(
    image_path: Path,
    title: str,
    output_path: Path,
    badge: str = "MAYOTTE",
) -> Path | None:
    """Génère la cover 1080x1920 de la vidéo : image héro + badge de série +
    titre 3-5 mots en gros. Sur la grille profil, TikTok superpose la
    description sur le bas de la vignette → rien sous les 80% de hauteur.
    Rendu via Pillow : drawtext FFmpeg plante sur ce build Windows
    (fontconfig), même piège que pour les sous-titres → ASS/PIL only.
    Best-effort : retourne None en cas d'échec (la cover est un bonus)."""
    font_path = FONTS_DIR / "Montserrat-Black.ttf"
    if not font_path.exists() or not image_path.exists():
        return None
    try:
        from PIL import Image, ImageDraw, ImageEnhance, ImageFont

        # Si le visuel héro est un clip VIDÉO (ex. fallback stock quand l'IA
        # est à quota), on en extrait une frame — Pillow ne lit pas les mp4.
        if _is_video(image_path):
            frame = output_path.with_suffix(".frame.png")
            r = subprocess.run(
                [FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                 "-ss", "0.5", "-i", str(image_path),
                 "-frames:v", "1", str(frame)],
                capture_output=True, text=True,
            )
            if r.returncode != 0 or not frame.exists():
                print("  ⚠️  Cover : extraction de frame vidéo échouée")
                return None
            image_path = frame

        img = Image.open(image_path).convert("RGB")
        # crop central vers 9:16 puis redimensionnement exact
        target_ratio = VIDEO_WIDTH / VIDEO_HEIGHT
        w, h = img.size
        if w / h > target_ratio:
            new_w = int(h * target_ratio)
            img = img.crop(((w - new_w) // 2, 0, (w + new_w) // 2, h))
        else:
            new_h = int(w / target_ratio)
            img = img.crop((0, (h - new_h) // 2, w, (h + new_h) // 2))
        img = img.resize((VIDEO_WIDTH, VIDEO_HEIGHT), Image.LANCZOS)
        # assombrit légèrement pour la lisibilité du titre
        img = ImageEnhance.Brightness(img).enhance(0.88)
        draw = ImageDraw.Draw(img, "RGBA")

        # Titre en majuscules, coupé en 2 lignes équilibrées au-delà de ~14 car.
        words = title.upper().split()
        lines = [" ".join(words)]
        if len(lines[0]) > 14 and len(words) >= 2:
            best, gap = 1, float("inf")
            for i in range(1, len(words)):
                a, b = " ".join(words[:i]), " ".join(words[i:])
                if abs(len(a) - len(b)) < gap:
                    best, gap = i, abs(len(a) - len(b))
            lines = [" ".join(words[:best]), " ".join(words[best:])]

        def fitted_font(text: str, max_size: int) -> "ImageFont.FreeTypeFont":
            size = max_size
            while size > 40:
                f = ImageFont.truetype(str(font_path), size)
                if draw.textlength(text, font=f) <= VIDEO_WIDTH - 160:
                    return f
                size -= 6
            return ImageFont.truetype(str(font_path), size)

        y = int(VIDEO_HEIGHT * 0.32)
        badge_font = ImageFont.truetype(str(font_path), 52)
        bw = draw.textlength(badge, font=badge_font)
        draw.text(((VIDEO_WIDTH - bw) / 2, y), badge, font=badge_font,
                  fill=(0, 240, 255), stroke_width=4, stroke_fill=(0, 0, 0))
        y += 110
        for line in lines:
            f = fitted_font(line, 118)
            lw = draw.textlength(line, font=f)
            lh = f.size
            # bandeau semi-transparent derrière le texte
            draw.rectangle(
                [(VIDEO_WIDTH - lw) / 2 - 24, y - 14,
                 (VIDEO_WIDTH + lw) / 2 + 24, y + lh + 18],
                fill=(0, 0, 0, 90),
            )
            draw.text(((VIDEO_WIDTH - lw) / 2, y), line, font=f,
                      fill=(255, 255, 255), stroke_width=7, stroke_fill=(0, 0, 0))
            y += int(lh * 1.3)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG")
        return output_path
    except Exception as e:
        print(f"  ⚠️  Cover : génération échouée ({e})")
        return None
