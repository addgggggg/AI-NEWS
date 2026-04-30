$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { $Python = "python" }

$Script = @"
from datetime import datetime, timezone
from app.config import load_settings
from app.logging_config import setup_logging
from app.collectors.base import CollectedItem
from app.pipeline.summarize import summarize
from run import get_llm_config

settings = load_settings()
setup_logging(settings.root_dir)
config = get_llm_config(settings)
print('provider=', config.provider)
print('model=', config.model)
print('base_url=', config.base_url)
print('api_key_configured=', bool(config.api_key))
item = CollectedItem(
    platform='test',
    external_id='test-1',
    title='AI company releases a new large model with stronger agent capabilities',
    author='test source',
    url='https://example.com/news/1',
    published_at=datetime.now(timezone.utc),
    description='This is a test item used only to verify whether the configured model endpoint works.',
)
report = summarize([item], config)
print('REPORT_START')
print(report[:1200])
print('REPORT_END')
"@

& $Python -c $Script
