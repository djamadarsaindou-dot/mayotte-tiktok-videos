# Alternative install script using schtasks (less strict than Register-ScheduledTask).
# Creates a task that runs the cron_loop.py at user logon.

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

# Delete previous task silently (ignore "not found" error)
& cmd /c "schtasks /delete /tn $TaskName /f 2>nul" | Out-Null

# schtasks via cmd /c (PowerShell mishandles spaces in /tr argument otherwise)
# Triple-escaped because: cmd parses /c "...", then schtasks parses /tr "..."
$cmdLine = "schtasks /create /tn $TaskName /tr `"\`"$PythonExe\`" \`"$CronScript\`"`" /sc ONLOGON /rl LIMITED /f"
Write-Host "Command: $cmdLine"
$result = & cmd /c $cmdLine 2>&1
Write-Host $result
if ($LASTEXITCODE -ne 0) {
    Write-Error "schtasks failed (exit $LASTEXITCODE)"
    exit 1
}

Write-Host "Task created: $TaskName" -ForegroundColor Green
Write-Host "  Trigger: at user logon (loop sleeps 6h internally)"
Write-Host ""
Write-Host "Start now (without rebooting):  schtasks /run /tn $TaskName"
Write-Host "Stop:                           schtasks /end /tn $TaskName"
Write-Host "Uninstall:                      schtasks /delete /tn $TaskName /f"
