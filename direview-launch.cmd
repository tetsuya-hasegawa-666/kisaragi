@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "LAUNCH_SCRIPT=C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-direview\tools\launch-dashboard.ps1"

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%LAUNCH_SCRIPT%" -DisplayRoot "%SCRIPT_DIR%"
