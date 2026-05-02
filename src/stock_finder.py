"""Trouve un asset visuel en essayant plusieurs sources dans l'ordre :

1. Pexels vidéo (générique mais qualité pro)
2. Pixabay vidéo
3. Wikimedia Commons photo (souvent Mayotte-spécifique)
4. Pexels photo
5. Pixabay photo
6. Pollinations IA (avec prompt enrichi Mayotte si possible)
"""
import random
from pathlib import Path

from src.images import generate_image
from src.stock_pixabay import search_photo as pixabay_photo
from src.stock_pixabay import search_video as pixabay_video
from src.stock_videos import search_photo as pexels_photo
from src.stock_videos import search_video as pexels_video
from src.stock_wikimedia import search_image as wikimedia_image


def find_asset(
    query: str,
    image_prompt_fallback: str,
    output_dir: Path,
    name: str,
    mayotte_specific: bool = False,
) -> tuple[Path, str]:
    """Renvoie (chemin, source). Lève si tout échoue.

    Si mayotte_specific=True, privilégie Wikimedia (souvent Mayotte) avant les
    stocks génériques.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    p_mp4 = output_dir / f"{name}.mp4"
    p_jpg = output_dir / f"{name}.jpg"

    if mayotte_specific:
        # Priorité à Wikimedia pour le contenu Mayotte spécifique
        if wikimedia_image(query, p_jpg):
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

    # Dernier recours : IA, prompt enrichi pour Mayotte si demandé
    base = image_prompt_fallback or query
    if mayotte_specific and "mayotte" not in base.lower():
        prompt = f"{base}, Mayotte Indian Ocean French overseas department, cinematic, vertical 9:16, no text, photorealistic"
    else:
        prompt = f"{base}, cinematic, vertical 9:16, no text, photorealistic"
    seed = random.randint(1, 1_000_000)
    generate_image(prompt, p_jpg, seed=seed)
    return p_jpg, "Pollinations IA"
