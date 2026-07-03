"""Alignement mot-à-mot de la voix off via faster-whisper.

Remplace les timings estimés de voice_coqui (distribution proportionnelle
à la longueur des mots : écart mesuré ~235 ms en moyenne, jusqu'à 935 ms)
par les timings réellement entendus par Whisper (~±20-100 ms).

Principe : on transcrit l'audio final avec word_timestamps=True, puis on
apparie les mots entendus aux mots EXACTS du texte source (difflib). Les
mots retournés sont toujours ceux du texte source, dans l'ordre, tous
présents — seuls les timings changent. Au moindre doute (ancrage < 70 %,
exception, audio trop court, faster-whisper indisponible), on rend les
timings estimés tels quels : l'alignement ne peut JAMAIS faire échouer
une génération.

PIÈGES MACHINE (validés par bench) :
- PyAV (av) est bloqué par Smart App Control → stub sys.modules["av"]
  AVANT d'importer faster_whisper, et audio passé en ndarray déjà décodé
  (soundfile + resample 16 kHz), jamais via decode_audio.
- Les DLL cudnn/cublas nécessaires à ctranslate2 sont dans <torch>/lib →
  os.add_dll_directory AVANT le chargement du modèle GPU.

Env : WHISPER_ALIGN=false désactive tout (fallback direct, aucun
chargement de modèle). Par défaut : activé.
"""
import difflib
import os
import re
import sys
import time
import types
import unicodedata
from pathlib import Path

# --- Stub PyAV : Smart App Control bloque les DLL de av. faster_whisper
# importe av au niveau module (audio.py) mais ne s'en sert que dans
# decode_audio(), qu'on n'appelle jamais (on passe un ndarray déjà décodé).
try:
    import av  # noqa: F401
except Exception:
    _av_stub = types.ModuleType("av")
    _av_stub.__doc__ = "Stub PyAV (DLL bloquées par Smart App Control)"
    sys.modules["av"] = _av_stub

# Import APRÈS le stub. S'il échoue (DLL, dépendance…), align_words
# rendra simplement les timings estimés — jamais d'exception qui remonte.
try:
    from faster_whisper import WhisperModel
except Exception as _e:  # pragma: no cover
    WhisperModel = None
    _IMPORT_ERROR = str(_e)
else:
    _IMPORT_ERROR = ""

WORD_RE = re.compile(r"\S+")
# Taux minimal de mots ancrés (appariés à l'identique) pour faire confiance
# à l'alignement Whisper. En dessous → timings estimés conservés.
MIN_ANCHOR_RATE = 0.70

_whisper = None


def _get_whisper():
    """Singleton faster-whisper "small" (calqué sur _get_tts de voice_coqui).

    GPU si le build torch le permet (RTX 5060 : ~0.5-0.7 s pour 11 s
    d'audio), sinon CPU int8. Téléchargement ~484 Mo au 1er run (cache HF).
    """
    global _whisper
    if _whisper is None:
        import torch
        # Les DLL cudnn/cublas dont ctranslate2 a besoin sont livrées avec
        # torch : il faut les rendre visibles AVANT le chargement GPU.
        torch_lib = Path(torch.__file__).resolve().parent / "lib"
        if os.name == "nt" and torch_lib.is_dir():
            os.add_dll_directory(str(torch_lib))
        if WhisperModel is None:
            raise RuntimeError(f"faster-whisper indisponible : {_IMPORT_ERROR}")
        if torch.cuda.is_available():
            device, compute = "cuda", "float16"
        else:
            device, compute = "cpu", "int8"
        print(f"   ⏳ Chargement Whisper small sur {device} "
              "(téléchargement ~484 Mo au 1er run)...")
        _whisper = WhisperModel("small", device=device, compute_type=compute)
    return _whisper


def _load_audio_16k(audio_path: Path):
    """Lit l'audio (mp3/wav) en mono float32 rééchantillonné à 16 kHz.

    soundfile lit le mp3 nativement (libsndfile 1.2+) ; en secours on
    décode via FFmpeg vers un WAV temporaire. Jamais via av/decode_audio
    (PyAV bloqué par Smart App Control).
    """
    import numpy as np
    import soundfile as sf
    try:
        data, sr = sf.read(str(audio_path), dtype="float32", always_2d=True)
    except Exception:
        # Secours : décodage FFmpeg → WAV temporaire mono 16 kHz
        import subprocess
        import tempfile
        from src.config import FFMPEG
        with tempfile.TemporaryDirectory() as td:
            wav = Path(td) / "align_tmp.wav"
            subprocess.run(
                [FFMPEG, "-y", "-i", str(audio_path),
                 "-ac", "1", "-ar", "16000", str(wav)],
                capture_output=True, check=True,
            )
            data, sr = sf.read(str(wav), dtype="float32", always_2d=True)
    mono = data.mean(axis=1).astype(np.float32)
    if sr != 16000:
        try:
            # Resample propre (torchaudio.functional = pur calcul torch,
            # aucune I/O → pas de souci torchcodec)
            import torch
            import torchaudio.functional as taf
            mono = taf.resample(torch.from_numpy(mono), sr, 16000).numpy()
        except Exception:
            # Secours numpy : interpolation linéaire (suffisant pour l'ASR)
            n_out = int(round(len(mono) * 16000 / sr))
            x_old = np.linspace(0.0, 1.0, num=len(mono), endpoint=False)
            x_new = np.linspace(0.0, 1.0, num=n_out, endpoint=False)
            mono = np.interp(x_new, x_old, mono).astype(np.float32)
    return np.ascontiguousarray(mono, dtype=np.float32), 16000


def _norm(word: str) -> str:
    """Normalise un mot pour l'appariement : NFD sans accents, minuscules,
    sans ponctuation (on ne garde que lettres/chiffres)."""
    nfd = unicodedata.normalize("NFD", word)
    sans_accents = "".join(c for c in nfd if not unicodedata.combining(c))
    return "".join(c for c in sans_accents if c.isalnum()).lower()


def _interpolate(src_words, i1, i2, t0, t1, starts, ends):
    """Répartit la fenêtre [t0, t1] sur les mots source i1..i2 au prorata
    de la longueur des mots (même logique que les timings estimés)."""
    if t1 < t0:
        t1 = t0
    weights = [max(1, len(_norm(w))) for w in src_words[i1:i2]]
    total = sum(weights)
    cursor = t0
    for k, wgt in enumerate(weights):
        d = (t1 - t0) * (wgt / total)
        starts[i1 + k] = cursor
        ends[i1 + k] = cursor + d
        cursor += d


def _match_words(src_words, hyp_words, audio_duration):
    """Apparie les mots source aux mots Whisper.

    - opcodes equal → timings Whisper directs (ancres) ;
    - replace 1:1 → appariement positionnel direct ;
    - spans n:m (ex. « mille cinq cents » ↔ « 1500 ») et mots non entendus →
      interpolation de la fenêtre temporelle du span au prorata des
      longueurs de mots, bornée par les mots Whisper voisins (ancres).

    Renvoie ([{word, start, end}], taux_ancrage).
    """
    src_norm = [_norm(w) for w in src_words]
    hyp_norm = [_norm(w["word"]) for w in hyp_words]
    sm = difflib.SequenceMatcher(a=src_norm, b=hyp_norm, autojunk=False)

    n = len(src_words)
    starts: list = [None] * n
    ends: list = [None] * n
    anchored = 0

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                starts[i1 + k] = hyp_words[j1 + k]["start"]
                ends[i1 + k] = hyp_words[j1 + k]["end"]
            anchored += i2 - i1
        elif tag == "replace" and (i2 - i1) == (j2 - j1):
            # Même nombre de mots : appariement positionnel direct
            for k in range(i2 - i1):
                starts[i1 + k] = hyp_words[j1 + k]["start"]
                ends[i1 + k] = hyp_words[j1 + k]["end"]
        elif tag in ("replace", "delete") and i2 > i1:
            # Span n:m — fenêtre temporelle du span côté Whisper, bornée
            # par les mots voisins si Whisper n'a rien entendu (delete).
            if j2 > j1:
                t0 = hyp_words[j1]["start"]
                t1 = hyp_words[j2 - 1]["end"]
            else:
                t0 = hyp_words[j1 - 1]["end"] if j1 > 0 else 0.0
                t1 = (hyp_words[j2]["start"] if j2 < len(hyp_words)
                      else audio_duration)
            _interpolate(src_words, i1, i2, t0, t1, starts, ends)
        # tag == "insert" : mots Whisper en trop, rien à assigner côté source

    # Filet : aucun trou, starts croissants (tolérance égalité), end ≥ start
    prev = 0.0
    for i in range(n):
        if starts[i] is None:
            starts[i] = prev
            ends[i] = prev
        if starts[i] < prev:
            starts[i] = prev
        if ends[i] < starts[i]:
            ends[i] = starts[i]
        prev = starts[i]

    items = [{"word": w, "start": float(s), "end": float(e)}
             for w, s, e in zip(src_words, starts, ends)]
    return items, anchored / max(1, n)


def align_words(audio_path: Path, text: str, fallback_words: list[dict]) -> list[dict]:
    """Aligne les mots du texte source sur l'audio via Whisper.

    Renvoie la même structure que les timings estimés :
    [{"word": <mot source EXACT>, "start": s, "end": s}] — mêmes mots,
    même ordre, timings précis. En cas de problème quelconque, renvoie
    fallback_words tel quel (jamais d'exception).
    """
    if os.getenv("WHISPER_ALIGN", "true").strip().lower() in ("false", "0", "no"):
        return fallback_words
    try:
        src_words = WORD_RE.findall(text)
        if not src_words:
            return fallback_words

        audio, sr = _load_audio_16k(Path(audio_path))
        duration = len(audio) / sr
        if duration < 1.0:
            print("   ⚠️ Alignement Whisper ignoré : audio < 1 s → timings estimés conservés")
            return fallback_words

        model = _get_whisper()
        t_start = time.perf_counter()
        # initial_prompt = début du texte source (limite 224 tokens) :
        # guide Whisper vers le vocabulaire exact (bench : matching 30/30)
        segments, _info = model.transcribe(
            audio,
            language="fr",
            word_timestamps=True,
            beam_size=5,
            initial_prompt=text[:200],
        )
        hyp_words = []
        for seg in segments:
            for w in (seg.words or []):
                hyp_words.append({"word": w.word.strip(),
                                  "start": float(w.start),
                                  "end": float(w.end)})
        if not hyp_words:
            print("   ⚠️ Alignement Whisper : transcription vide → timings estimés conservés")
            return fallback_words

        aligned, anchor_rate = _match_words(src_words, hyp_words, duration)
        if anchor_rate < MIN_ANCHOR_RATE:
            print(f"   ⚠️ Alignement Whisper : ancrage {anchor_rate:.0%} < "
                  f"{MIN_ANCHOR_RATE:.0%} → timings estimés conservés")
            return fallback_words

        elapsed = time.perf_counter() - t_start
        print(f"   🎯 Alignement Whisper : {len(aligned)} mots, "
              f"ancrage {anchor_rate:.0%}, {elapsed:.1f}s")
        return aligned
    except Exception as e:
        print(f"   ⚠️ Alignement Whisper échoué ({e}) → timings estimés conservés")
        return fallback_words
