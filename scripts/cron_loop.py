"""Boucle qui génère une vidéo TikTok à heures fixes (08h, 12h, 16h, 20h).

Plus fiable que Task Scheduler Windows (qui plante avec Ctrl+C externes).
Lancé au démarrage Windows (cf. install_cron_loop.ps1 / dossier Startup).

Logique :
1. (option --now) génère une vidéo immédiatement
2. Calcule le prochain créneau horaire aligné sur l'horloge
3. Dort jusqu'à ce créneau
4. Génère une vidéo + nettoie les anciennes
5. Recommence

Créneaux alignés sur l'horloge : les vidéos sortent à des heures FIXES et
prévisibles, et redémarrer le cron ne décale pas le planning.

Tout est loggé dans logs/cron_loop_YYYY-MM-DD_HH-MM-SS.log.

Usage :
    python scripts/cron_loop.py           # démarre, attend le 1er créneau
    python scripts/cron_loop.py --now     # démarre + génère tout de suite
"""
import argparse
import datetime as dt
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Heures de génération (24h). 2 vidéos/jour (matin + soir) pour rester dans
# le quota Cloudflare gratuit en mode 100% images IA (2 × 48 = 96 img/jour).
SLOT_HOURS = [8, 18]

PYTHON_EXE = ROOT / ".venv" / "Scripts" / "python.exe"
GENERATE_SCRIPT = ROOT / "generate_video.py"
CLEANUP_SCRIPT = ROOT / "scripts" / "cleanup_videos.py"
LOG_DIR = ROOT / "logs"
LOCK_FILE = LOG_DIR / "cron.lock"
STATE_FILE = LOG_DIR / "last_generation.txt"

# Après une génération en échec, attendre avant de retenter (évite de
# marteler les API si une clé est morte ou le réseau coupé).
RETRY_DELAY = dt.timedelta(hours=2)

_log_file = None


def _open_log() -> None:
    """Ouvre un fichier de log dédié à ce lancement du cron."""
    global _log_file
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    try:
        _log_file = open(LOG_DIR / f"cron_loop_{ts}.log", "a", encoding="utf-8")
    except Exception:
        _log_file = None


def log(msg: str) -> None:
    """Logge à la fois sur stdout et dans le fichier de log du cron."""
    line = f"[{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    if _log_file:
        try:
            _log_file.write(line + "\n")
            _log_file.flush()
        except Exception:
            pass


def acquire_lock() -> bool:
    """Verrou anti-doublon : empêche 2 cron_loop simultanés."""
    from src.locking import acquire
    return acquire(LOCK_FILE)


def next_slot(now: dt.datetime | None = None) -> dt.datetime:
    """Retourne le datetime du prochain créneau horaire (strictement futur)."""
    now = now or dt.datetime.now()
    candidates: list[dt.datetime] = []
    for day_offset in (0, 1):
        day = now.date() + dt.timedelta(days=day_offset)
        for h in SLOT_HOURS:
            slot = dt.datetime.combine(day, dt.time(hour=h))
            if slot > now:
                candidates.append(slot)
    return min(candidates)


def last_passed_slot(now: dt.datetime | None = None) -> dt.datetime:
    """Retourne le datetime du dernier créneau déjà passé (ou en cours)."""
    now = now or dt.datetime.now()
    candidates: list[dt.datetime] = []
    for day_offset in (0, -1):
        day = now.date() + dt.timedelta(days=day_offset)
        for h in SLOT_HOURS:
            slot = dt.datetime.combine(day, dt.time(hour=h))
            if slot <= now:
                candidates.append(slot)
    return max(candidates)


def read_last_generation() -> dt.datetime | None:
    """Date de la dernière génération réussie, ou None si jamais enregistrée."""
    try:
        return dt.datetime.fromisoformat(
            STATE_FILE.read_text(encoding="utf-8").strip())
    except Exception:
        return None


def write_last_generation(when: dt.datetime | None = None) -> None:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(
            (when or dt.datetime.now()).isoformat(), encoding="utf-8")
    except Exception as e:
        log(f"⚠️  Impossible d'écrire {STATE_FILE.name} : {e}")


def run_one(label: str, cmd: list[str]) -> int:
    log(f"▶ {label}")
    t0 = time.time()
    result = subprocess.run(cmd, cwd=str(ROOT))
    dur = time.time() - t0
    log(f"✓ {label} terminé en {dur:.0f}s (exit code {result.returncode})")
    return result.returncode


def generate_and_cleanup() -> bool:
    """Génère une vidéo puis nettoie les anciennes (best-effort).

    Retourne True si la génération a réussi ; dans ce cas la date est
    enregistrée dans STATE_FILE (base du rattrapage anacron)."""
    ok = False
    try:
        rc = run_one("Génération vidéo", [str(PYTHON_EXE), str(GENERATE_SCRIPT)])
        ok = rc == 0
    except Exception as e:
        log(f"❌ Génération a levé une exception : {e}")
    if ok:
        write_last_generation()
    try:
        run_one("Nettoyage anciennes vidéos",
                [str(PYTHON_EXE), str(CLEANUP_SCRIPT)])
    except Exception as e:
        log(f"⚠️  Nettoyage a levé : {e}")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Cron de génération vidéo TikTok")
    parser.add_argument("--now", action="store_true",
                        help="Génère une vidéo immédiatement au démarrage")
    args = parser.parse_args()

    _open_log()
    if not acquire_lock():
        log("⚠️  Une instance du cron tourne déjà — arrêt de ce doublon.")
        return 0

    log(f"🚀 Cron loop démarré — créneaux quotidiens : "
        f"{', '.join(f'{h:02d}h' for h in SLOT_HOURS)}")
    log(f"   Project root : {ROOT}")

    if not PYTHON_EXE.exists():
        log(f"❌ Python venv introuvable : {PYTHON_EXE}")
        return 1

    last_attempt: dt.datetime | None = None
    if args.now:
        log("━━━ Génération immédiate (--now) ━━━")
        last_attempt = dt.datetime.now()
        generate_and_cleanup()

    # Boucle anacron : un créneau est « dû » tant que la dernière génération
    # réussie est antérieure au dernier créneau passé. Le PC éteint ou en
    # veille à 8h/18h n'est donc plus un problème — on rattrape au réveil.
    # Sommeil par tranches de 5 min : time.sleep ne compte pas le temps de
    # veille Windows, une longue attente d'un bloc raterait le créneau.
    announced: dt.datetime | None = None
    while True:
        now = dt.datetime.now()
        due_slot = last_passed_slot(now)
        last_gen = read_last_generation()
        due = last_gen is None or last_gen < due_slot
        throttled = (last_attempt is not None
                     and now - last_attempt < RETRY_DELAY)

        if due and not throttled:
            late = now - due_slot > dt.timedelta(minutes=5)
            label = "Rattrapage créneau manqué" if late else "Créneau"
            log(f"━━━ {label} {due_slot.strftime('%d/%m %H:%M')} ━━━")
            last_attempt = now
            generate_and_cleanup()
            announced = None
            continue

        target = next_slot(now)
        if due and throttled:
            target = min(target, last_attempt + RETRY_DELAY)
        if announced != target:
            log(f"💤 Prochaine génération à {target.strftime('%Y-%m-%d %H:%M')}")
            announced = target
        time.sleep(min(300, max(1, (target - dt.datetime.now()).total_seconds())))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        log("👋 Arrêt manuel demandé")
        sys.exit(130)
