param(
    [string]$TaskName = "AI News Agent Auto"
)

$ErrorActionPreference = "Stop"
Start-ScheduledTask -TaskName $TaskName
Get-ScheduledTask -TaskName $TaskName | Select-Object TaskName, State
