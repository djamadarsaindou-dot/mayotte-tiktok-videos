@echo off
REM Lancement par le Task Scheduler Windows toutes les 2h.
REM Génère une vidéo + nettoie les anciennes (garde N plus récentes).

set "PROJECT=C:\Users\djama\Documents\Claude\Projects\Site internet - Montage vidéo"
cd /d "%PROJECT%"

set "PYTHONIOENCODING=utf-8"
set "LOG_DIR=%PROJECT%\logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

set "TS=%date:~6,4%-%date:~3,2%-%date:~0,2%_%time:~0,2%-%time:~3,2%-%time:~6,2%"
set "TS=%TS: =0%"
set "LOG=%LOG_DIR%\cron_%TS%.log"

echo === CRON %date% %time% === > "%LOG%"
".venv\Scripts\python.exe" generate_video.py >> "%LOG%" 2>&1
".venv\Scripts\python.exe" "scripts\cleanup_videos.py" >> "%LOG%" 2>&1
echo === FIN %date% %time% === >> "%LOG%"
