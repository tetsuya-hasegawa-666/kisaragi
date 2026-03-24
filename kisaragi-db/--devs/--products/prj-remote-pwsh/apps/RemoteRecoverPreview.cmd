@echo off
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\Invoke-RemoteRecover.ps1" -WhatIf
pause
