@echo off
cd /d "%~dp0"
echo Close ChatGPT completely before running this repair.
echo This only prepares the current runtime cache. The app stays on its current drive.
python "%~dp0repair_runtime.py" --repair
echo.
pause
