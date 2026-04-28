param(
    [string]$ShortcutName = "AI News Agent Auto.cmd"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$RunCmd = Join-Path $ProjectRoot "scripts\run_auto.cmd"

if (-not (Test-Path $RunCmd)) {
    throw "Run cmd was not found: $RunCmd"
}

$StartupDir = [Environment]::GetFolderPath("Startup")
$StartupFile = Join-Path $StartupDir $ShortcutName

$Content = @"
@echo off
call "$RunCmd"
"@

Set-Content -LiteralPath $StartupFile -Value $Content -Encoding ASCII

Write-Host "Installed startup command:"
Write-Host $StartupFile
Write-Host "It will run after the current user logs into Windows."
