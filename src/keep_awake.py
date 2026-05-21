"""Empêche Windows de se mettre en veille pendant une opération longue.

Sans ça, si l'utilisateur ferme le capot du laptop ou laisse l'ordi inactif,
Windows met le système en veille → le process Python est gelé (une génération
de 15 min peut sembler durer 5h si l'ordi dort entre-temps).

Utilisation :
    from src.keep_awake import keep_awake
    with keep_awake():
        ... opération longue ...

⚠️ Limite : SetThreadExecutionState empêche la veille par INACTIVITÉ, mais ne
bloque PAS la veille déclenchée par la fermeture du capot. Pour ça, il faut
configurer Windows (« À la fermeture du capot → Ne rien faire ») — voir
scripts/setup_power.py.
"""
from __future__ import annotations

import sys
from contextlib import contextmanager

# Constantes de l'API Windows SetThreadExecutionState
ES_CONTINUOUS = 0x80000000        # le réglage reste actif jusqu'à annulation
ES_SYSTEM_REQUIRED = 0x00000001   # empêche la mise en veille du système
ES_DISPLAY_REQUIRED = 0x00000002  # empêche aussi l'extinction de l'écran


@contextmanager
def keep_awake(keep_display: bool = False):
    """Context manager : empêche la veille tant que le bloc s'exécute.

    keep_display=True garde aussi l'écran allumé (utile en debug, inutile
    pour un cron headless).
    """
    if sys.platform != "win32":
        # macOS/Linux : pas d'équivalent simple → on ne fait rien.
        yield
        return

    import ctypes

    flags = ES_CONTINUOUS | ES_SYSTEM_REQUIRED
    if keep_display:
        flags |= ES_DISPLAY_REQUIRED

    applied = False
    try:
        result = ctypes.windll.kernel32.SetThreadExecutionState(flags)
        applied = result != 0
        if applied:
            print("  ☕ Veille système désactivée (génération en cours)")
    except Exception as e:
        print(f"  ℹ️  keep_awake indisponible : {e}")

    try:
        yield
    finally:
        if applied:
            try:
                # ES_CONTINUOUS seul = on rend la main au comportement normal.
                ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
                print("  ☕ Veille système réactivée")
            except Exception:
                pass
