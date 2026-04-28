param(
    [string]$ShortcutName = "AI News Agent Auto.cmd"
)

$ErrorActionPreference = "Stop"
$StartupDir = [Environment]::GetFolderPath("Startup")
$StartupFile = Join-Path $StartupDir $ShortcutName

if (Test-Path $StartupFile) {
    Remove-Item -LiteralPath $StartupFile -Force
    Write-Host "Removed startup command:"
    Write-Host $StartupFile
} else {
    Write-Host "Startup command not found:"
    Write-Host $StartupFile
}
