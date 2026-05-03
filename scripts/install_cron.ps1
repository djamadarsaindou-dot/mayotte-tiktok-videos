# Installe une tâche planifiée Windows qui génère une vidéo TikTok toutes les 2h.
#
# Lancer une fois en PowerShell :
#   powershell -ExecutionPolicy Bypass -File scripts\install_cron.ps1
#
# Pour désinstaller :
#   Unregister-ScheduledTask -TaskName "MayotteTikTokGen" -Confirm:$false

$ErrorActionPreference = "Stop"

$ProjectPath = "C:\Users\djama\Documents\Claude\Projects\Site internet - Montage vidéo"
$BatPath = Join-Path $ProjectPath "scripts\run_cron.bat"
$TaskName = "MayotteTikTokGen"

if (-not (Test-Path $BatPath)) {
    Write-Error "Fichier introuvable : $BatPath"
    exit 1
}

# Désinstalle la tâche existante si présente
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Suppression de l'ancienne tâche..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Action : exécuter le .bat
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$BatPath`""

# Trigger : toutes les 2h, à partir de dans 5 minutes
$startTime = (Get-Date).AddMinutes(5)
$trigger = New-ScheduledTaskTrigger -Once -At $startTime `
    -RepetitionInterval (New-TimeSpan -Hours 2) `
    -RepetitionDuration ([TimeSpan]::FromDays(3650))  # ~10 ans

# Settings : démarre dès que possible si manqué, ne pas arrêter sur idle, timeout 50min
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopOnIdleEnd `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 50) `
    -MultipleInstances IgnoreNew `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries

# Principal : exécution sous le user courant, sans demander de mdp à chaque fois
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Génère une vidéo TikTok Mayotte toutes les 2h (Coqui XTTS + Mistral + Pollinations IA)"

Write-Host ""
Write-Host "✅ Tâche planifiée installée : $TaskName" -ForegroundColor Green
Write-Host "   Démarrage : $startTime"
Write-Host "   Répétition : toutes les 2 heures"
Write-Host ""
Write-Host "Commandes utiles :"
Write-Host "  Get-ScheduledTask -TaskName MayotteTikTokGen"
Write-Host "  Start-ScheduledTask -TaskName MayotteTikTokGen   # lancer maintenant"
Write-Host "  Unregister-ScheduledTask -TaskName MayotteTikTokGen -Confirm:`$false   # désinstaller"
Write-Host ""
Write-Host "Logs : $ProjectPath\logs\"
