@echo off
echo This launcher will run remote resume.
set /p CONFIRM=Type YES to continue: 
if /I not "%CONFIRM%"=="YES" goto :EOF
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\Invoke-RemoteResume.ps1"
pause
