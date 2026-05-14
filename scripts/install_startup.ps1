# Installs the cron loop via the Windows Startup folder (no Task Scheduler needed).
# Works even when corporate policy blocks Register-ScheduledTask.
#
# Run from project root: powershell -ExecutionPolicy Bypass -File scripts\install_startup.ps1

$ErrorActionPreference = "Stop"

$ProjectPath = (Get-Location).Path
$PythonExe = Join-Path $ProjectPath ".venv\Scripts\python.exe"
$CronScript = Join-Path $ProjectPath "scripts\cron_loop.py"
$StartupDir = [Environment]::GetFolderPath("Startup")
$BatTarget = Join-Path $StartupDir "MayotteTikTokLoop.bat"

if (-not (Test-Path $PythonExe)) {
    Write-Error "Python venv not found: $PythonExe"
    exit 1
}
if (-not (Test-Path $CronScript)) {
    Write-Error "Cron script not found: $CronScript"
    exit 1
}

# Write a .bat file in the Startup folder
$batContent = @"
@echo off
REM Mayotte TikTok video generation - auto-launched at Windows logon
REM Loops internally every 6 hours. Logs in <project>\logs\
title Mayotte TikTok Generator (cron 6h)
set "PYTHONIOENCODING=utf-8"
set "PYTHONUNBUFFERED=1"
cd /d "$ProjectPath"
"$PythonExe" "$CronScript"
"@

# Encoding ASCII to avoid UTF-8 BOM issues with cmd
[System.IO.File]::WriteAllText($BatTarget, $batContent, [System.Text.Encoding]::Default)

Write-Host "Bat installed at: $BatTarget" -ForegroundColor Green
Write-Host ""
Write-Host "It will auto-launch at the next Windows logon."
Write-Host "To start NOW without rebooting:"
Write-Host "  Start-Process `"$BatTarget`""
Write-Host ""
Write-Host "To uninstall:"
Write-Host "  Remove-Item `"$BatTarget`""
