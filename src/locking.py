"""Verrou mono-instance : empêche 2 exécutions simultanées d'un même script.

Basé sur un fichier lock contenant le PID. Le verrou est :
- atomique (création exclusive O_EXCL — un seul process gagne la course)
- auto-récupérable (si le PID du lock est mort, on récupère le verrou)
- auto-libéré à la fin du process (atexit)

Usage :
    from src.locking import acquire
    if not acquire(LOCK_DIR / "generate.lock"):
        print("Déjà en cours, on s'arrête.")
        sys.exit(0)
"""
import atexit
import os
import subprocess
from pathlib import Path


def _pid_alive(pid: int) -> bool:
    """Vrai si un process avec ce PID tourne. Prudent : True si on ne sait pas."""
    try:
        import psutil
        return psutil.pid_exists(pid)
    except Exception:
        pass
    try:
        out = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}"],
            capture_output=True, text=True,
        )
        return str(pid) in out.stdout
    except Exception:
        return True  # incertain → on suppose vivant (ne casse pas un lock légitime)


def _release_if_owned(lock_path: Path, my_pid: int) -> None:
    """Libère le verrou UNIQUEMENT s'il nous appartient encore.

    Sans cette vérification, un process qui se termine effacerait le verrou
    même s'il a entre-temps été (légitimement) repris par un autre process —
    ce qui ouvre la porte à des doublons en cascade.
    """
    try:
        if (lock_path.exists()
                and lock_path.read_text(encoding="utf-8").strip() == str(my_pid)):
            lock_path.unlink(missing_ok=True)
    except Exception:
        pass


def acquire(lock_path: Path) -> bool:
    """Tente d'acquérir le verrou. True = acquis, False = déjà pris par un autre."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    # Lock résiduel d'un run précédent tué brutalement → purge si PID mort
    if lock_path.exists():
        try:
            old_pid = int(lock_path.read_text().strip())
            if old_pid != os.getpid() and _pid_alive(old_pid):
                return False  # une autre instance VIVANTE détient le verrou
            lock_path.unlink(missing_ok=True)
        except Exception:
            lock_path.unlink(missing_ok=True)

    # Création EXCLUSIVE atomique : un seul process gagne si plusieurs tentent
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
    except FileExistsError:
        return False

    atexit.register(_release_if_owned, lock_path, os.getpid())
    return True
