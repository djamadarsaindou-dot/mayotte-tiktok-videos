"""Génère les LUTs .cube de la chaîne (identité visuelle du grading).

Trois looks candidats sont produits dans assets/luts/ ; celui retenu est
copié sous le nom `mayotte_signature.cube` (c'est LUI que editor.py charge).
Regénérer : `.venv/Scripts/python.exe scripts/make_luts.py`
"""
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
LUT_DIR = ROOT / "assets" / "luts"
SIZE = 33  # résolution standard des LUT .cube

# Look retenu comme identité visuelle de la chaîne (voir choix en bas)
SIGNATURE = "teal_orange"


def _luma(r, g, b):
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _smooth_contrast(x, amount):
    """Courbe en S douce autour de 0.5 (amount 0..1)."""
    return x + amount * (x - 0.5) * (1.0 - np.abs(2.0 * x - 1.0)) * 0.5


def _saturate(r, g, b, factor):
    y = _luma(r, g, b)
    return (y + (r - y) * factor,
            y + (g - y) * factor,
            y + (b - y) * factor)


def look_teal_orange(r, g, b):
    """Teal & orange doux : ombres bleutées, hautes lumières chaudes.
    Le classique cinéma — très flatteur pour lagon + peaux."""
    r, g, b = (_smooth_contrast(c, 0.35) for c in (r, g, b))
    y = _luma(r, g, b)
    shadows = np.clip(1.0 - y * 1.8, 0.0, 1.0)      # poids des ombres
    highs = np.clip((y - 0.55) * 2.2, 0.0, 1.0)     # poids des hautes lumières
    r = r - 0.035 * shadows + 0.045 * highs
    g = g + 0.008 * shadows + 0.012 * highs
    b = b + 0.050 * shadows - 0.045 * highs
    r, g, b = _saturate(r, g, b, 1.10)
    return r, g, b


def look_golden_hour(r, g, b):
    """Golden hour : tout réchauffé, noirs légèrement délavés (pellicule)."""
    r, g, b = (_smooth_contrast(c, 0.25) for c in (r, g, b))
    y = _luma(r, g, b)
    warm = 0.5 + 0.5 * y
    r = r + 0.045 * warm
    g = g + 0.015 * warm
    b = b - 0.035 * warm
    # noirs relevés façon film
    r, g, b = (0.03 + c * 0.97 for c in (r, g, b))
    r, g, b = _saturate(r, g, b, 1.06)
    return r, g, b


def look_tropical_punch(r, g, b):
    """Tropical punch : contraste marqué, cyans/bleus du lagon dopés."""
    r, g, b = (_smooth_contrast(c, 0.50) for c in (r, g, b))
    y = _luma(r, g, b)
    blueness = np.clip(b - np.maximum(r, g), 0.0, 1.0)
    b = b + 0.06 * blueness
    g = g + 0.03 * blueness
    highs = np.clip((y - 0.6) * 2.0, 0.0, 1.0)
    r = r + 0.03 * highs
    r, g, b = _saturate(r, g, b, 1.16)
    return r, g, b


LOOKS = {
    "teal_orange": look_teal_orange,
    "golden_hour": look_golden_hour,
    "tropical_punch": look_tropical_punch,
}


def write_cube(name: str, fn) -> Path:
    grid = np.linspace(0.0, 1.0, SIZE)
    b, g, r = np.meshgrid(grid, grid, grid, indexing="ij")
    r2, g2, b2 = fn(r.copy(), g.copy(), b.copy())
    out = np.stack([c.reshape(-1) for c in (r2, g2, b2)], axis=1)
    out = np.clip(out, 0.0, 1.0)
    path = LUT_DIR / f"{name}.cube"
    lines = [f"TITLE \"{name}\"", f"LUT_3D_SIZE {SIZE}", ""]
    lines += [f"{p[0]:.6f} {p[1]:.6f} {p[2]:.6f}" for p in out]
    path.write_text("\n".join(lines) + "\n", encoding="ascii")
    return path


def main() -> int:
    LUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, fn in LOOKS.items():
        p = write_cube(name, fn)
        print(f"LUT écrite : {p} ({p.stat().st_size // 1024} ko)")
    src = LUT_DIR / f"{SIGNATURE}.cube"
    dst = LUT_DIR / "mayotte_signature.cube"
    shutil.copyfile(src, dst)
    print(f"Signature de la chaîne : {SIGNATURE} → {dst.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
