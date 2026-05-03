# Install a Windows scheduled task that generates a TikTok video every 2 hours.
#
# Run once in PowerShell:
#   powershell -ExecutionPolicy Bypass -File scripts\install_cron.ps1
#
# To uninstall:
#   Unregister-ScheduledTask -TaskName "MayotteTikTokGen" -Confirm:$false

$ErrorActionPreference = "Stop"

# Construit le chemin du projet a partir du dossier courant (le user doit lancer
# le script depuis la racine du projet)
$ProjectPath = (Get-Location).Path
$BatPath = Join-Path $ProjectPath "scripts\run_cron.bat"
$TaskName = "MayotteTikTokGen"

if (-not (Test-Path $BatPath)) {
    Write-Error "Script not found: $BatPath`nLance ce script depuis la racine du projet (cd `"...Site internet - Montage video`")."
    exit 1
}

# Remove existing task if present
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Action: run the .bat
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$BatPath`""

# Trigger: every 2h, starting in 5 minutes
$startTime = (Get-Date).AddMinutes(5)
$trigger = New-ScheduledTaskTrigger -Once -At $startTime `
    -RepetitionInterval (New-TimeSpan -Hours 2) `
    -RepetitionDuration ([TimeSpan]::FromDays(3650))

# Settings
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopOnIdleEnd `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 50) `
    -MultipleInstances IgnoreNew `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries

# Principal: run as current user, interactive
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Mayotte TikTok video generation every 2 hours"

Write-Host ""
Write-Host "Task installed: $TaskName" -ForegroundColor Green
Write-Host "  Start: $startTime"
Write-Host "  Interval: every 2 hours"
Write-Host ""
Write-Host "Useful commands:"
Write-Host "  Get-ScheduledTask -TaskName MayotteTikTokGen"
Write-Host "  Start-ScheduledTask -TaskName MayotteTikTokGen     # run now"
Write-Host "  Unregister-ScheduledTask -TaskName MayotteTikTokGen -Confirm:`$false   # uninstall"
Write-Host ""
Write-Host "Logs: $ProjectPath\logs\"
