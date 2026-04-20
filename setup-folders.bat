@echo off
REM Setup Video Category Folders
cd /d "%~dp0"
python3 scripts\setup-video-folders.py
pause
