# Setup Telemetry Upload Task (Windows)
#
# This script configures a Windows Task Scheduler task to run telemetry upload every hour.

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$PythonPath = Join-Path $ProjectRoot "openclass-env\Scripts\python.exe"
$CronScript = Join-Path $ScriptDir "telemetry_upload_cron.py"
$LogsDir = Join-Path $ProjectRoot "logs"

Write-Host "Setting up telemetry upload scheduled task..."
Write-Host "Project root: $ProjectRoot"
Write-Host "Python path: $PythonPath"
Write-Host "Cron script: $CronScript"

# Ensure logs directory exists
if (-not (Test-Path $LogsDir)) {
    New-Item -ItemType Directory -Path $LogsDir | Out-Null
}

# Task name
$TaskName = "NexusAI-TelemetryUpload"

# Check if task already exists
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($ExistingTask) {
    Write-Host "Task '$TaskName' already exists"
    Write-Host "Removing existing task..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create task action
$Action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument $CronScript `
    -WorkingDirectory $ProjectRoot

# Create task trigger (hourly)
$Trigger = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Hours 1) `
    -RepetitionDuration ([TimeSpan]::MaxValue)

# Create task settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false

# Register task
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Uploads NexusAI telemetry metrics to DynamoDB every hour" `
    -User "SYSTEM" `
    -RunLevel Highest

Write-Host ""
Write-Host "Task '$TaskName' created successfully"
Write-Host "Task will run every hour"
Write-Host "Logs will be written to: $LogsDir\telemetry_upload.log"
Write-Host ""
Write-Host "To view task: Get-ScheduledTask -TaskName '$TaskName'"
Write-Host "To remove task: Unregister-ScheduledTask -TaskName '$TaskName'"
Write-Host ""
Write-Host "Setup complete!"
