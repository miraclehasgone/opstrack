@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "OPSTRACK_PY=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
if not exist "%OPSTRACK_PY%" set "OPSTRACK_PY=python"
start "" "http://127.0.0.1:4173/"
"%OPSTRACK_PY%" -m http.server 4173 --directory dist
