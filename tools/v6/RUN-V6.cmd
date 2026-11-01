@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN-V6.ps1"
if errorlevel 1 (
 echo.
 echo FAILED: No validated firmware was produced. Do not flash partial images.
) else (
 echo.
 echo Workflow completed. Check report in chosen output folder.
)
pause
