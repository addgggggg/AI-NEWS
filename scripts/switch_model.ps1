param(
    [string]$Profile,
    [switch]$List
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$ProfilesPath = Join-Path $ProjectRoot "config\model_profiles.yaml"
$EnvPath = Join-Path $ProjectRoot ".env"

function Load-Profiles {
    $profiles = @{}
    $currentKey = $null
    foreach ($line in Get-Content -LiteralPath $ProfilesPath -Encoding UTF8) {
        if ($line -match '^  ([A-Za-z0-9_-]+):\s*$') {
            $currentKey = $Matches[1]
            $profiles[$currentKey] = @{}
            continue
        }
        if ($currentKey -and $line -match '^\s{4}([A-Za-z0-9_-]+):\s*(.*)\s*$') {
            $field = $Matches[1]
            $value = $Matches[2].Trim().Trim('"').Trim("'")
            $profiles[$currentKey][$field] = $value
        }
    }
    return $profiles
}

$Profiles = Load-Profiles

if ($List -or -not $Profile) {
    Write-Host "Available model profiles:"
    foreach ($key in ($Profiles.Keys | Sort-Object)) {
        $item = $Profiles[$key]
        Write-Host ("- {0}: {1} | provider={2} | model={3} | base_url={4}" -f $key, $item["label"], $item["provider"], $item["model"], $item["base_url"])
    }
    if (-not $Profile) {
        Write-Host ""
        Write-Host "Usage:"
        Write-Host "  scripts\switch_model.ps1 -Profile deepseek"
    }
    exit 0
}

if (-not $Profiles.ContainsKey($Profile)) {
    Write-Error "Unknown profile: $Profile. Available: $($Profiles.Keys -join ', ')"
    exit 2
}

$Selected = $Profiles[$Profile]
if (-not (Test-Path $EnvPath)) {
    @(
        "LLM_API_KEY="
        "LLM_MODEL="
        "LLM_BASE_URL="
        "FEISHU_WEBHOOK="
        "AI_NEWS_CONFIG=config.yaml"
    ) | Set-Content -LiteralPath $EnvPath -Encoding UTF8
}

$Values = @{
    "LLM_MODEL" = $Selected["model"]
    "LLM_BASE_URL" = $Selected["base_url"]
}

$seen = @{}
$output = New-Object System.Collections.Generic.List[string]
foreach ($line in Get-Content -LiteralPath $EnvPath -Encoding UTF8) {
    if ($line.Trim() -eq "" -or $line.TrimStart().StartsWith("#") -or $line -notmatch "=") {
        $output.Add($line)
        continue
    }
    $key = $line.Split("=", 2)[0].Trim()
    if ($Values.ContainsKey($key)) {
        $output.Add("$key=$($Values[$key])")
        $seen[$key] = $true
    } else {
        $output.Add($line)
    }
}

foreach ($key in $Values.Keys) {
    if (-not $seen.ContainsKey($key)) {
        $output.Add("$key=$($Values[$key])")
    }
}

$output | Set-Content -LiteralPath $EnvPath -Encoding UTF8

Write-Host "Switched model profile: $Profile"
Write-Host "Label: $($Selected["label"])"
Write-Host "Provider: $($Selected["provider"])"
Write-Host "Model: $($Selected["model"])"
Write-Host "Base URL: $($Selected["base_url"])"
Write-Host "Note: LLM_API_KEY is not changed. Put the matching provider key in .env."
