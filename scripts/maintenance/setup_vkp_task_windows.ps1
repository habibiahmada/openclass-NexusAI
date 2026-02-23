# Setup VKP Pull Task (Windows)
#
# This script sets up the hourly VKP pull task on Windows systems using Task Scheduler.
#
# Usage:
#   Run as Administrator:
#   powershell -ExecutionPolicy Bypass -File scripts\setup_vkp_task_windows.ps1

# Requires Administrator privileges
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "This script must be run as Administrator"
    exit 1
}

Write-Host "Setting up VKP Pull Scheduled Task..." -ForegroundColor Green

# Get project root directory
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Write-Host "Project root: $ProjectRoot"

# Create logs directory
$LogsDir = Join-Path $ProjectRoot "logs"
if (-not (Test-Path $LogsDir)) {
    New-Item -ItemType Directory -Path $LogsDir | Out-Null
}

# Get Python path
$PythonPath = (Get-Command python).Source
if (-not $PythonPath) {
    Write-Error "Python not found in PATH. Please install Python 3.9+ and add to PATH."
    exit 1
}
Write-Host "Python path: $PythonPath"

# Script path
$ScriptPath = Join-Path $ProjectRoot "scripts\vkp_pull_cron.py"
$LogPath = Join-Path $ProjectRoot "logs\vkp_pull.log"

# Task name
$TaskName = "NexusAI-VKP-Pull"

# Check if task already exists
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Write-Host "Task already exists. Removing old task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create task action
$Action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "`"$ScriptPath`"" `
    -WorkingDirectory $ProjectRoot

# Create task trigger (daily, repeat every 1 hour)
$Trigger = New-ScheduledTaskTrigger `
    -Daily `
    -At "00:00" `
    -RepetitionInterval (New-TimeSpan -Hours 1) `
    -RepetitionDuration (New-TimeSpan -Days 1)

# Create task settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

# Create task principal (run as SYSTEM)
$Principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

# Register task
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Hourly VKP pull from AWS S3 for OpenClass Nexus AI" | Out-Null

Write-Host "✓ VKP pull scheduled task created successfully" -ForegroundColor Green
Write-Host "  Task name: $TaskName"
Write-Host "  Schedule: Every hour"
Write-Host "  Log file: $LogPath"

# Verify task
Write-Host ""
Write-Host "Task details:" -ForegroundColor Cyan
Get-ScheduledTask -TaskName $TaskName | Format-List TaskName, State, Triggers

Write-Host ""
Write-Host "To manually run the VKP pull:" -ForegroundColor Cyan
Write-Host "  python `"$ScriptPath`""

Write-Host ""
Write-Host "To view task history:" -ForegroundColor Cyan
Write-Host "  Open Task Scheduler -> Task Scheduler Library -> $TaskName"

Write-Host ""
Write-Host "To view logs:" -ForegroundColor Cyan
Write-Host "  Get-Content `"$LogPath`" -Tail 50 -Wait"

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
