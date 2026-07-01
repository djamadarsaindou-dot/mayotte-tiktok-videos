"""Bench Z-Image-Turbo (ModelScope) vs Cloudflare FLUX schnell — 5 images.

Piste identifiée par la recherche de juillet 2026 : Z-Image-Turbo génère en
864x1536 (portrait 9:16 quasi natif) avec un palier gratuit ModelScope.

PRÉ-REQUIS (à faire UNE fois, manuellement) :
  1. Créer un compte sur https://modelscope.cn (liaison Alibaba Cloud requise,
     vérification d'identité — faisable hors Chine).
  2. Générer un token API : https://modelscope.cn/my/myaccesstoken
  3. L'ajouter au .env : MODELSCOPE_API_KEY=ms-xxxx

Usage : .venv/Scripts/python.exe scripts/bench_zimage.py
Sortie : output/zimage_bench/ — 5 images Z-Image + 5 images FLUX (mêmes
prompts) + planche contact comparative à envoyer sur le téléphone.
"""
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.net import SESSION  # noqa: E402

API_BASE = "https://api-inference.modelscope.cn/v1"
OUT_DIR = ROOT / "output" / "zimage_bench"

PROMPTS = [
    "Aerial drone view of a turquoise double barrier reef lagoon, Mayotte "
    "island, Indian Ocean, warm golden hour light, soft shadows, cinematic",
    "Traditional Mahoran woman applying msindzano sandalwood face mask, "
    "portrait, warm golden hour light, soft shadows, cinematic",
    "Fishermen pulling djarifa net in shallow tropical water at sunrise, "
    "Mayotte, warm golden hour light, cinematic documentary",
    "Baobab tree silhouette on white sand beach, green sea turtle tracks, "
    "Mayotte island, warm golden hour light, cinematic",
    "Colorful market stalls with tropical fruits and spices, Mamoudzou "
    "Mayotte, bustling morning, warm light, cinematic documentary",
]


def zimage_generate(prompt: str, out_path: Path, api_key: str) -> float:
    """Lance une génération asynchrone Z-Image-Turbo et attend le résultat."""
    t0 = time.time()
    r = SESSION.post(
        f"{API_BASE}/images/generations",
        headers={"Authorization": f"Bearer {api_key}",
                 "X-ModelScope-Async-Mode": "true"},
        json={"model": "Tongyi-MAI/Z-Image-Turbo",
              "prompt": prompt, "size": "864x1536"},
        timeout=60,
    )
    r.raise_for_status()
    task_id = r.json()["task_id"]
    for _ in range(60):  # polling max ~6 min
        time.sleep(6)
        s = SESSION.get(
            f"{API_BASE}/tasks/{task_id}",
            headers={"Authorization": f"Bearer {api_key}",
                     "X-ModelScope-Task-Type": "image_generation"},
            timeout=30,
        )
        s.raise_for_status()
        data = s.json()
        if data.get("task_status") == "SUCCEED":
            img_url = data["output_images"][0]
            img = SESSION.get(img_url, timeout=120)
            img.raise_for_status()
            out_path.write_bytes(img.content)
            return time.time() - t0
        if data.get("task_status") == "FAILED":
            raise RuntimeError(f"Tâche échouée : {json.dumps(data)[:300]}")
    raise TimeoutError("Z-Image : polling expiré (6 min)")


def main() -> int:
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except Exception:
        pass
    api_key = os.getenv("MODELSCOPE_API_KEY", "").strip()
    if not api_key:
        print(__doc__)
        print("❌ MODELSCOPE_API_KEY absente du .env — suis les PRÉ-REQUIS "
              "ci-dessus puis relance.")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    from src.stock_finder import find_ai_asset  # Cloudflare FLUX actuel

    print("── Z-Image-Turbo (ModelScope) ──")
    for i, prompt in enumerate(PROMPTS):
        out = OUT_DIR / f"zimage_{i+1}.jpg"
        try:
            dt = zimage_generate(prompt, out, api_key)
            from PIL import Image
            print(f"  [{i+1}/5] {dt:.0f}s {Image.open(out).size} → {out.name}")
        except Exception as e:
            print(f"  [{i+1}/5] ÉCHEC : {e}")

    print("── Cloudflare FLUX schnell (mêmes prompts) ──")
    for i, prompt in enumerate(PROMPTS):
        try:
            t0 = time.time()
            asset = find_ai_asset(
                query=prompt, image_prompt_fallback=prompt,
                output_dir=OUT_DIR, name=f"flux_{i+1}",
                mayotte_specific=False, seed_key=f"bench-{i}",
            )
            print(f"  [{i+1}/5] {time.time()-t0:.0f}s → {asset}")
        except Exception as e:
            print(f"  [{i+1}/5] ÉCHEC : {e}")

    print(f"\n📂 Compare les images dans : {OUT_DIR}")
    print("   Si Z-Image gagne → on l'intègre en provider primaire "
          "(Cloudflare en fallback).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
