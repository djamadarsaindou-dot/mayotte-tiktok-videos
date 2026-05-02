"""Trouve un asset visuel (vidéo ou image) en essayant plusieurs sources.

Ordre : Pexels vidéo → Pixabay vidéo → Pexels photo → Pixabay photo → Pollinations IA
"""
import random
from pathlib import Path

from src.images import generate_image
from src.stock_pixabay import search_photo as pixabay_photo
from src.stock_pixabay import search_video as pixabay_video
from src.stock_videos import search_photo as pexels_photo
from src.stock_videos import search_video as pexels_video


def find_asset(query: str, image_prompt_fallback: str, output_dir: Path, name: str) -> tuple[Path, str]:
    """Renvoie (chemin, source). Lève seulement si tout échoue."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1) Pexels vidéo
    p = output_dir / f"{name}.mp4"
    if pexels_video(query, p):
        return p, "Pexels vidéo"

    # 2) Pixabay vidéo
    if pixabay_video(query, p):
        return p, "Pixabay vidéo"

    # 3) Pexels photo
    p_jpg = output_dir / f"{name}.jpg"
    if pexels_photo(query, p_jpg):
        return p_jpg, "Pexels photo"

    # 4) Pixabay photo
    if pixabay_photo(query, p_jpg):
        return p_jpg, "Pixabay photo"

    # 5) Pollinations IA (dernier recours, lent)
    prompt = (image_prompt_fallback or query) + ", cinematic, vertical 9:16, no text"
    seed = random.randint(1, 1_000_000)
    generate_image(prompt, p_jpg, seed=seed)
    return p_jpg, "Pollinations IA"
