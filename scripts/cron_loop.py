"""Boucle infinie qui génère une vidéo TikTok toutes les 6h.

Plus fiable que Task Scheduler Windows (qui plante avec Ctrl+C externes).
Lancé au démarrage Windows via Task Scheduler "AtLogon" (cf. install_cron_loop.ps1).

Logique :
1. Génère une vidéo (peut prendre 20-40 min avec Coqui + Pollinations IA)
2. Nettoie les anciennes vidéos (garde N plus récentes)
3. Calcule le temps écoulé, dort jusqu'au prochain créneau de 6h
4. Recommence

Tout est loggé dans logs/cron_loop_YYYY-MM-DD_HH-MM-SS.log.
"""
import atexit
import datetime as dt
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

INTERVAL_HOURS = 6
INTERVAL_SECONDS = INTERVAL_HOURS * 3600

PYTHON_EXE = ROOT / ".venv" / "Scripts" / "python.exe"
GENERATE_SCRIPT = ROOT / "generate_video.py"
CLEANUP_SCRIPT = ROOT / "scripts" / "cleanup_videos.py"
LOG_DIR = ROOT / "logs"


LOCK_FILE = LOG_DIR / "cron.lock"


def _pid_alive(pid: int) -> bool:
    """Vrai si un process avec ce PID tourne actuellement."""
    try:
        import psutil
        return psutil.pid_exists(pid)
    except Exception:
        # Fallback sans psutil : tasklist
        try:
            out = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True, text=True,
            )
            return str(pid) in out.stdout
        except Exception:
            return False


def acquire_lock() -> bool:
    """Verrou anti-doublon : empêche 2 cron_loop de tourner en même temps.

    Renvoie True si le verrou est acquis, False si une instance tourne déjà.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if LOCK_FILE.exists():
        try:
            old_pid = int(LOCK_FILE.read_text().strip())
            if old_pid != os.getpid() and _pid_alive(old_pid):
                return False  # une autre instance tourne
        except Exception:
            pass  # lock corrompu → on le récupère
    LOCK_FILE.write_text(str(os.getpid()), encoding="utf-8")
    atexit.register(lambda: LOCK_FILE.unlink(missing_ok=True))
    return True


def now_str() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(msg: str) -> None:
    print(f"[{now_str()}] {msg}", flush=True)


def run_one(label: str, cmd: list[str]) -> int:
    log(f"▶ {label}")
    t0 = time.time()
    result = subprocess.run(cmd, cwd=str(ROOT))
    dur = time.time() - t0
    log(f"✓ {label} terminé en {dur:.0f}s (exit code {result.returncode})")
    return result.returncode


def sleep_until_next_slot(start_time: float) -> None:
    elapsed = time.time() - start_time
    wait = INTERVAL_SECONDS - elapsed
    if wait <= 0:
        log("⚠️  Génération + nettoyage ont dépassé l'intervalle — redémarrage immédiat")
        return
    next_run = dt.datetime.now() + dt.timedelta(seconds=wait)
    log(f"💤 Sommeil {wait/3600:.2f}h — prochaine génération à "
        f"{next_run.strftime('%Y-%m-%d %H:%M')}")
    time.sleep(wait)


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if not acquire_lock():
        log("⚠️  Une instance du cron tourne déjà — arrêt de ce doublon.")
        return 0

    log(f"🚀 Cron loop démarré (intervalle {INTERVAL_HOURS}h)")
    log(f"   Project root : {ROOT}")
    log(f"   Python venv  : {PYTHON_EXE}")

    if not PYTHON_EXE.exists():
        log(f"❌ Python venv introuvable : {PYTHON_EXE}")
        return 1

    iteration = 0
    while True:
        iteration += 1
        log(f"━━━ Itération #{iteration} ━━━")
        slot_start = time.time()
        try:
            run_one("Génération vidéo", [str(PYTHON_EXE), str(GENERATE_SCRIPT)])
        except Exception as e:
            log(f"❌ Génération a levé une exception : {e}")
        try:
            run_one("Nettoyage anciennes vidéos",
                    [str(PYTHON_EXE), str(CLEANUP_SCRIPT)])
        except Exception as e:
            log(f"⚠️  Nettoyage a levé : {e}")
        sleep_until_next_slot(slot_start)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        log("👋 Arrêt manuel demandé")
        sys.exit(130)
