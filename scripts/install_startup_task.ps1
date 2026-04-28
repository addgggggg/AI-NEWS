param(
    [string]$TaskName = "AI News Agent Auto",
    [switch]$Interactive
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$RunScript = Join-Path $ProjectRoot "scripts\run_auto.ps1"
$RunCmd = Join-Path $ProjectRoot "scripts\run_auto.cmd"

if (-not (Test-Path $RunScript)) {
    throw "Run script was not found: $RunScript"
}
if (-not (Test-Path $RunCmd)) {
    throw "Run cmd was not found: $RunCmd"
}

$TaskCommand = "`"$RunCmd`""
$SchTasks = Join-Path $env:SystemRoot "System32\schtasks.exe"

$PreviousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $SchTasks /Query /TN $TaskName *> $null
$QueryExitCode = $LASTEXITCODE
$ErrorActionPreference = $PreviousErrorActionPreference
if ($QueryExitCode -eq 0) {
    & $SchTasks /Delete /TN $TaskName /F | Out-Null
}

if ($Interactive) {
    & $SchTasks /Create /TN $TaskName /SC ONLOGON /TR $TaskCommand /IT /F | Out-Null
} else {
    & $SchTasks /Create /TN $TaskName /SC ONLOGON /TR $TaskCommand /F | Out-Null
}

if ($LASTEXITCODE -ne 0) {
    throw "Failed to create scheduled task. Try running PowerShell as Administrator."
}

Write-Host "Installed startup task: $TaskName"
Write-Host "It will run at user logon."
Write-Host "To start it now:"
Write-Host "Start-ScheduledTask -TaskName `"$TaskName`""
