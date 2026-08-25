@echo off
chcp 65001 > nul
title GazeAlert Studio • AI Eye Tracking Suite
cls

echo ============================================================
echo   🚀 GazeAlert Studio - Pornire aplicatie...
echo ============================================================
echo.

cd /d "%~dp0"

:: 1. Lansare instantanee a aplicatiei Python
python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] A aparut o problema la pornire. Verificare dependente...
    pip install -r requirements.txt
    python main.py
    pause
)
