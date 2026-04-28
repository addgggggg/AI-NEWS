@echo off
set "PROJECT_ROOT=%~dp0.."
cd /d "%PROJECT_ROOT%"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\scripts\run_auto.ps1"
