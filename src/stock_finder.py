"""Trouve un asset visuel en essayant plusieurs sources.

Provider IA : Cloudflare Workers AI (FLUX-schnell) si configuré, sinon
Pollinations en repli. Voir src/cloudflare_images.py et src/images.py.

Mode `ai_first` (défaut) : IA → Pexels → Pixabay → Wikimedia
  → idéal pour des images en CORRÉLATION FORTE avec le texte.

Mode `stock_first` : Pexels vidéo → Pixabay vidéo → Wikimedia → IA
  → plus rapide, contenu visuel plus générique.

Mode hybride utilisé par generate_video.py : 1er visuel de chaque scène en IA
  (ancre du sens), les autres en stock pour la rapidité. Deux fonctions sont
  exposées : `find_ai_asset` et `find_stock_asset`.

Mode smart mix (VISUALS_SMART_MIX) : les scènes taguées « ambiance » par le
  LLM utilisent de VRAIS clips vidéo (Pexels portrait, mouvement réel =
  meilleure rétention), les scènes « specifique » restent en image IA.
  Le routage est décidé par `decide_visual_route`, les clips récurrents
  (lagon, tortue, maki…) sont mis en cache disque (LRU) dans assets/stock_cache/.
"""
import os
import re
import shutil
import threading
import time
import zlib
from pathlib import Path

from src import cloudflare_images
from src.cloudflare_images import CloudflareUnavailable
from src.config import (
    PEXELS_API_KEY,
    STOCK_CACHE_DIR,
    STOCK_CACHE_MAX_FILES,
    STOCK_CLIP_MAX_MB,
    VISUAL_PROVIDER,
    VISUALS_AI_ONLY,
    VISUALS_SMART_MIX,
)
from src.images import PollinationsUnavailable
from src.images import generate_image as pollinations_generate_image
from src.stock_pixabay import search_photo as pixabay_photo
from src.stock_pixabay import search_video as pixabay_video
from src.stock_videos import search_photo as pexels_photo
from src.stock_videos import search_video as pexels_video
from src.stock_wikimedia import search_image as wikimedia_image

# Exceptions « IA définitivement indisponible » — quel que soit le provider,
# le caller ne doit pas réessayer mais basculer en fallback stock.
AI_UNAVAILABLE = (PollinationsUnavailable, CloudflareUnavailable)

# Variations d'angle par index du visuel dans la scène : les 4 visuels d'une
# scène partagent le même image_prompt + le même seed déterministe — ce
# suffixe garantit 4 cadrages différents SANS appel LLM supplémentaire.
SHOT_VARIATIONS = [
    "wide establishing shot",
    "medium shot, eye level",
    "close-up detail shot",
    "high angle shot from above",
]


def deterministic_seed(key: str) -> int:
    """Seed déterministe inter-runs à partir d'une clé texte.

    zlib.crc32 et non hash() : le hash() Python est salé par processus
    (PYTHONHASHSEED) donc non reproductible d'un run à l'autre."""
    return zlib.crc32(key.encode("utf-8")) % 1_000_000


def _ai_generate(query: str, image_prompt_fallback: str, output_path: Path,
                 mayotte_specific: bool, seed_key: str | None = None,
                 shot_index: int | None = None, seed_offset: int = 0) -> Path:
    """Génère une image IA. Cloudflare en priorité (gratuit, fiable),
    Pollinations en repli si Cloudflare n'est pas configuré dans .env.

    seed_key : clé de seed déterministe (ex. "topic-3") — reproductible d'un
    run à l'autre. Sans clé, on dérive le seed du prompt lui-même.
    shot_index : index du visuel dans la scène → variation d'angle du prompt.
    seed_offset : décalage pour obtenir une image différente au retry."""
    base = image_prompt_fallback or query
    # FLUX-schnell génère carré → « centered composition » pour que le sujet
    # survive au recadrage 9:16 effectué ensuite par le montage FFmpeg.
    suffix = ", cinematic, centered composition, no text, photorealistic"
    if mayotte_specific and "mayotte" not in base.lower():
        prompt = f"{base}, Mayotte Indian Ocean French overseas department{suffix}"
    else:
        prompt = base + suffix
    if shot_index is not None:
        # Angle différent pour chaque visuel de la scène (plan large / moyen /
        # détail / plongée) — varie les cadrages sans varier le sujet.
        prompt += ", " + SHOT_VARIATIONS[shot_index % len(SHOT_VARIATIONS)]
    seed = (deterministic_seed(seed_key or prompt) + seed_offset) % 1_000_000
    if cloudflare_images.is_configured():
        cloudflare_images.generate_image(prompt, output_path, seed=seed)
    else:
        pollinations_generate_image(prompt, output_path, seed=seed)
    return output_path


def find_asset(
    query: str,
    image_prompt_fallback: str,
    output_dir: Path,
    name: str,
    mayotte_specific: bool = False,
    seed_key: str | None = None,
    shot_index: int | None = None,
) -> tuple[Path, str]:
    """Renvoie (chemin, source). Lève si tout échoue."""
    output_dir.mkdir(parents=True, exist_ok=True)

    p_mp4 = output_dir / f"{name}.mp4"
    p_jpg = output_dir / f"{name}.jpg"

    if VISUAL_PROVIDER == "ai_first":
        # 1) Image IA en PRIORITÉ ABSOLUE (qualité IA = exigence utilisateur).
        # 2 tentatives avec des seeds différents avant de céder au fallback stock.
        for ai_attempt in range(2):
            try:
                _ai_generate(query, image_prompt_fallback, p_jpg, mayotte_specific,
                             seed_key=seed_key, shot_index=shot_index,
                             seed_offset=ai_attempt)
                return p_jpg, "IA"
            except AI_UNAVAILABLE:
                # Erreur définitive (service payant/quota épuisé) : pas de retry.
                break
            except Exception as e:
                print(f"  ⚠️  Image IA tentative {ai_attempt+1}/2 a échoué : "
                      f"{str(e)[:80]}")
        print(f"  ↪  Bascule fallback stock pour : {query[:60]}")

        # 2) Fallback : Pexels vidéo
        if pexels_video(query, p_mp4):
            return p_mp4, "Pexels vidéo (fallback)"
        # 3) Pixabay vidéo
        if pixabay_video(query, p_mp4):
            return p_mp4, "Pixabay vidéo (fallback)"
        # 4) Wikimedia
        if wikimedia_image(query, p_jpg, force_mayotte=mayotte_specific):
            return p_jpg, "Wikimedia (fallback)"
        # 5) Pexels photo
        if pexels_photo(query, p_jpg):
            return p_jpg, "Pexels photo (fallback)"
        # 6) Pixabay photo
        if pixabay_photo(query, p_jpg):
            return p_jpg, "Pixabay photo (fallback)"
        raise RuntimeError(f"Aucune source n'a pu fournir un visuel pour : {query}")

    # Mode stock_first (legacy)
    if mayotte_specific and wikimedia_image(query, p_jpg, force_mayotte=True):
        return p_jpg, "Wikimedia (Mayotte)"
    if pexels_video(query, p_mp4):
        return p_mp4, "Pexels vidéo"
    if pixabay_video(query, p_mp4):
        return p_mp4, "Pixabay vidéo"
    if not mayotte_specific and wikimedia_image(query, p_jpg):
        return p_jpg, "Wikimedia"
    if pexels_photo(query, p_jpg):
        return p_jpg, "Pexels photo"
    if pixabay_photo(query, p_jpg):
        return p_jpg, "Pixabay photo"
    _ai_generate(query, image_prompt_fallback, p_jpg, mayotte_specific,
                 seed_key=seed_key, shot_index=shot_index)
    return p_jpg, "IA"


# ─────────────────────────────────────────────────────────────────────────────
# Mode hybride (mix IA + stock par scène)
# ─────────────────────────────────────────────────────────────────────────────

def find_ai_asset(
    query: str,
    image_prompt_fallback: str,
    output_dir: Path,
    name: str,
    mayotte_specific: bool = False,
    seed_key: str | None = None,
    shot_index: int | None = None,
    full_stock_fallback: bool = False,
) -> tuple[Path, str]:
    """Force la génération IA. Si tout échoue :
    - full_stock_fallback=True (mode smart mix) : chaîne stock COMPLÈTE
      Pexels → Pixabay → Wikimedia (vidéos puis photos)
    - sinon (legacy) : fallback Pexels uniquement (rapide)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    p_jpg = output_dir / f"{name}.jpg"
    p_mp4 = output_dir / f"{name}.mp4"

    for ai_attempt in range(2):
        try:
            _ai_generate(query, image_prompt_fallback, p_jpg, mayotte_specific,
                         seed_key=seed_key, shot_index=shot_index,
                         seed_offset=ai_attempt)
            return p_jpg, "IA"
        except AI_UNAVAILABLE:
            # Erreur définitive (service payant/quota épuisé) : pas de retry.
            break
        except Exception as e:
            print(f"  ⚠️  IA tentative {ai_attempt+1}/2 a échoué : {str(e)[:70]}")

    print(f"  ↪  IA indisponible, fallback stock pour : {query[:50]}")
    if pexels_video(query, p_mp4):
        return p_mp4, "Pexels vidéo (IA-fallback)"
    if full_stock_fallback:
        # Chaîne stock complète (mode smart mix) : Pexels → Pixabay → Wikimedia
        if pixabay_video(query, p_mp4):
            return p_mp4, "Pixabay vidéo (IA-fallback)"
        if wikimedia_image(query, p_jpg, force_mayotte=mayotte_specific):
            return p_jpg, "Wikimedia (IA-fallback)"
    if pexels_photo(query, p_jpg):
        return p_jpg, "Pexels photo (IA-fallback)"
    if full_stock_fallback and pixabay_photo(query, p_jpg):
        return p_jpg, "Pixabay photo (IA-fallback)"
    raise RuntimeError(f"Aucune source pour : {query}")


def find_stock_asset(
    query: str,
    image_prompt_fallback: str,
    output_dir: Path,
    name: str,
    mayotte_specific: bool = False,
    seed_key: str | None = None,
    shot_index: int | None = None,
) -> tuple[Path, str]:
    """Stock d'abord (rapide), IA en dernier recours uniquement."""
    output_dir.mkdir(parents=True, exist_ok=True)
    p_jpg = output_dir / f"{name}.jpg"
    p_mp4 = output_dir / f"{name}.mp4"

    if pexels_video(query, p_mp4):
        return p_mp4, "Pexels vidéo"
    if pixabay_video(query, p_mp4):
        return p_mp4, "Pixabay vidéo"
    if mayotte_specific and wikimedia_image(query, p_jpg, force_mayotte=True):
        return p_jpg, "Wikimedia (Mayotte)"
    if pexels_photo(query, p_jpg):
        return p_jpg, "Pexels photo"
    if pixabay_photo(query, p_jpg):
        return p_jpg, "Pixabay photo"
    if not mayotte_specific and wikimedia_image(query, p_jpg):
        return p_jpg, "Wikimedia"

    # Dernier recours : IA même en stock_first
    try:
        _ai_generate(query, image_prompt_fallback, p_jpg, mayotte_specific,
                     seed_key=seed_key, shot_index=shot_index)
        return p_jpg, "IA (stock-fallback)"
    except Exception:
        raise RuntimeError(f"Aucune source pour : {query}")


# ─────────────────────────────────────────────────────────────────────────────
# Mode SMART MIX (scènes « ambiance » → vrais clips vidéo, « specifique » → IA)
# ─────────────────────────────────────────────────────────────────────────────

def decide_visual_route(
    visual_kind: str,
    visual_idx: int = 0,
    ai_only: bool | None = None,
    smart_mix: bool | None = None,
) -> str:
    """Décide la source d'un visuel : "ai", "stock_clip" ou "stock".

    Priorités (rétro-compatibilité) :
    1. VISUALS_AI_ONLY=true → tout en IA (comportement historique conservé)
    2. VISUALS_SMART_MIX=true → scène "ambiance" → vrai clip vidéo stock,
       scène "specifique" → image IA
    3. sinon → mode hybride legacy (1er visuel IA, les autres stock)

    ai_only / smart_mix : surcharges pour les tests unitaires (sinon config).
    """
    if ai_only is None:
        ai_only = VISUALS_AI_ONLY
    if smart_mix is None:
        smart_mix = VISUALS_SMART_MIX
    if ai_only:
        return "ai"
    if smart_mix:
        kind = str(visual_kind or "").strip().lower()
        return "stock_clip" if kind == "ambiance" else "ai"
    return "ai" if visual_idx == 0 else "stock"


# --- Cache disque des clips stock récurrents (lagon, tortue, maki, marché…) ---
# Clé = requête normalisée. LRU sur le mtime : au-delà de N fichiers, les
# moins récemment utilisés sont supprimés (~35 Go libres seulement).
_cache_lock = threading.Lock()


def _cache_key(query: str) -> str:
    """Normalise une requête en clé de cache stable (slug + crc32)."""
    slug = re.sub(r"[^a-z0-9]+", "-", query.strip().lower()).strip("-")[:60]
    return f"{slug or 'clip'}-{zlib.crc32(query.strip().lower().encode('utf-8')):08x}"


def _cache_lookup(query: str, output_path: Path) -> Path | None:
    """Copie le clip depuis le cache s'il existe (et rafraîchit son mtime LRU)."""
    cached = STOCK_CACHE_DIR / f"{_cache_key(query)}.mp4"
    if not cached.exists():
        return None
    try:
        shutil.copy2(cached, output_path)
        os.utime(cached, (time.time(), time.time()))  # marque « utilisé récemment »
        return output_path
    except Exception:
        return None


def _cache_store(query: str, clip_path: Path) -> None:
    """Ajoute un clip au cache et applique la limite LRU (best-effort)."""
    try:
        with _cache_lock:
            STOCK_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            dest = STOCK_CACHE_DIR / f"{_cache_key(query)}.mp4"
            shutil.copy2(clip_path, dest)
            # copy2 préserve le mtime SOURCE → on force « maintenant » pour
            # que l'ordre LRU (basé mtime) reflète bien le dernier usage.
            os.utime(dest, (time.time(), time.time()))
            # Éviction LRU : supprime les plus anciens au-delà de la limite
            files = sorted(STOCK_CACHE_DIR.glob("*.mp4"),
                           key=lambda p: p.stat().st_mtime, reverse=True)
            for old in files[STOCK_CACHE_MAX_FILES:]:
                old.unlink(missing_ok=True)
    except Exception as e:
        print(f"  ℹ️  Cache stock : écriture ignorée ({str(e)[:60]})")


def _pexels_portrait_clip(query: str, output_path: Path) -> Path | None:
    """Télécharge un clip Pexels portrait en variante LÉGÈRE (~720p, ≤10 Mo).

    Contrairement à stock_videos.search_video (qui prend la plus grande
    variante, parfois 4K/50 Mo), on vise la variante ~720p et on coupe le
    téléchargement au-delà de STOCK_CLIP_MAX_MB — connexion fragile à Mayotte.
    """
    if not PEXELS_API_KEY:
        return None
    from src.net import SESSION

    try:
        r = SESSION.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={"query": query, "orientation": "portrait",
                    "size": "medium", "per_page": 8},
            timeout=60,
        )
        r.raise_for_status()
        videos = r.json().get("videos", [])
    except Exception as e:
        print(f"  ⚠️  Pexels clip échec '{query[:40]}' : {str(e)[:70]}")
        return None

    max_bytes = int(STOCK_CLIP_MAX_MB * 1024 * 1024)
    # Clips de 3 à 30 s (assez longs pour la coupe, pas de fichiers énormes)
    pool = [v for v in videos if 3 <= v.get("duration", 0) <= 30] or videos
    for video in pool:
        files = [f for f in video.get("video_files", [])
                 if f.get("file_type") == "video/mp4"
                 and f.get("height", 0) >= f.get("width", 0)   # portrait
                 and f.get("width", 0) >= 700]                 # ≥ ~720p
        # Variante la plus légère d'abord (largeur minimale ≥ 720)
        files.sort(key=lambda f: (f.get("width", 0), f.get("height", 0)))
        for chosen in files[:2]:
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                written = 0
                with SESSION.get(chosen["link"], stream=True, timeout=60) as dl:
                    dl.raise_for_status()
                    with output_path.open("wb") as f:
                        for chunk in dl.iter_content(chunk_size=65536):
                            if not chunk:
                                continue
                            written += len(chunk)
                            if written > max_bytes:
                                raise RuntimeError("clip > taille max, on passe")
                            f.write(chunk)
                if output_path.stat().st_size > 100_000:
                    return output_path
            except Exception as e:
                output_path.unlink(missing_ok=True)
                print(f"  ⚠️  Téléchargement clip Pexels : {str(e)[:60]}")
                continue
    return None


def find_ambiance_clip(
    query: str,
    image_prompt_fallback: str,
    output_dir: Path,
    name: str,
    mayotte_specific: bool = False,
    seed_key: str | None = None,
    shot_index: int | None = None,
) -> tuple[Path, str]:
    """Visuel de scène « ambiance » : VRAI clip vidéo en priorité.

    Ordre : cache disque → Pexels portrait léger → Pixabay vidéo → image IA
    (avec chaîne stock complète en dernier filet via find_ai_asset).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    p_mp4 = output_dir / f"{name}.mp4"

    # 1) Cache disque des clips récurrents (lagon, tortue, maki, marché…)
    if _cache_lookup(query, p_mp4):
        return p_mp4, "Clip (cache)"

    # 2) Pexels portrait ~720p ≤ 10 Mo
    if _pexels_portrait_clip(query, p_mp4):
        _cache_store(query, p_mp4)
        return p_mp4, "Pexels clip"

    # 3) Pixabay vidéo
    if pixabay_video(query, p_mp4):
        _cache_store(query, p_mp4)
        return p_mp4, "Pixabay clip"

    # 4) Pas de clip trouvé : image IA comme pour une scène « specifique »
    # (find_ai_asset retombe lui-même sur la chaîne stock complète si l'IA
    # échoue — Pexels → Pixabay → Wikimedia).
    return find_ai_asset(
        query, image_prompt_fallback, output_dir, name,
        mayotte_specific=mayotte_specific, seed_key=seed_key,
        shot_index=shot_index, full_stock_fallback=True,
    )
