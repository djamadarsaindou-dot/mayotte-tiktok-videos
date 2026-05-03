@echo off
REM Launched by Windows Task Scheduler every 2 hours.
REM Generates a video then cleans old ones (keeps N most recent).
REM Auto-detects project path from this script's location (no hardcoded accent).

setlocal
set "SCRIPT_DIR=%~dp0"
REM Strip "scripts\" (8 chars) from script dir to get project root with trailing backslash
set "PROJECT=%SCRIPT_DIR:~0,-8%"
cd /d "%PROJECT%"

set "PYTHONIOENCODING=utf-8"
set "LOG_DIR=%PROJECT%logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

set "TS=%date:~6,4%-%date:~3,2%-%date:~0,2%_%time:~0,2%-%time:~3,2%-%time:~6,2%"
set "TS=%TS: =0%"
set "LOG=%LOG_DIR%\cron_%TS%.log"

echo === CRON %date% %time% === > "%LOG%"
echo Project: %PROJECT% >> "%LOG%"
".venv\Scripts\python.exe" generate_video.py >> "%LOG%" 2>&1
".venv\Scripts\python.exe" "scripts\cleanup_videos.py" >> "%LOG%" 2>&1
echo === END %date% %time% === >> "%LOG%"
endlocal
