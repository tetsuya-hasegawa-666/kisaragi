@echo off
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\Invoke-RemoteDoctor.ps1" -Format Table
pause
