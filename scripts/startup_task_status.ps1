param(
    [string]$TaskName = "AI News Agent Auto"
)

$ErrorActionPreference = "Stop"
$Task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $Task) {
    Write-Host "Startup task not found: $TaskName"
    exit 1
}

$Info = Get-ScheduledTaskInfo -TaskName $TaskName
$Task | Select-Object TaskName, State
$Info | Select-Object LastRunTime, LastTaskResult, NextRunTime, NumberOfMissedRuns
