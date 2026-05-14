# Install a Windows scheduled task that launches the cron_loop.py at user logon.
# The Python script then handles the 6h interval itself (more reliable than
# Task Scheduler's RepetitionInterval which had Ctrl+C issues for us).
#
# Run from project root:
#   powershell -ExecutionPolicy Bypass -File scripts\install_cron_loop.ps1
#
# Uninstall:
#   Unregister-ScheduledTask -TaskName "MayotteTikTokLoop" -Confirm:$false

$ErrorActionPreference = "Stop"

$ProjectPath = (Get-Location).Path
$PythonExe = Join-Path $ProjectPath ".venv\Scripts\python.exe"
$CronScript = Join-Path $ProjectPath "scripts\cron_loop.py"
$TaskName = "MayotteTikTokLoop"

if (-not (Test-Path $PythonExe)) {
    Write-Error "Python venv not found: $PythonExe"
    exit 1
}
if (-not (Test-Path $CronScript)) {
    Write-Error "Cron script not found: $CronScript"
    exit 1
}

# Remove old task if present
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Also remove the old 2h task if it still exists
$old = Get-ScheduledTask -TaskName "MayotteTikTokGen" -ErrorAction SilentlyContinue
if ($old) {
    Write-Host "Removing old MayotteTikTokGen task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName "MayotteTikTokGen" -Confirm:$false
}

# Action: run cron_loop.py with the venv python, working dir = project root
$action = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument "`"$CronScript`"" `
    -WorkingDirectory $ProjectPath

# Trigger: at user logon
$trigger = New-ScheduledTaskTrigger -AtLogOn

# Settings: never time out, restart on failure, allow on battery
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopOnIdleEnd `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5)

# Run as current user, interactive (visible console)
$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Mayotte TikTok video generation loop (Python sleeps 6h between videos)"

Write-Host ""
Write-Host "Task installed: $TaskName" -ForegroundColor Green
Write-Host "  Triggers at: user logon"
Write-Host "  Internal loop interval: 6 hours"
Write-Host "  Restart on failure: yes (3 retries, 5 min apart)"
Write-Host ""
Write-Host "To start the loop now (without rebooting):"
Write-Host "  Start-ScheduledTask -TaskName $TaskName"
Write-Host ""
Write-Host "To stop:"
Write-Host "  Stop-ScheduledTask -TaskName $TaskName"
Write-Host ""
Write-Host "To uninstall:"
Write-Host "  Unregister-ScheduledTask -TaskName $TaskName -Confirm:`$false"
