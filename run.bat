@echo off
title GazeAlert Studio AI Suite
cls

echo ============================================================
echo   [+] GazeAlert Studio - Pornire aplicatie...
echo ============================================================
echo.

cd /d "%~dp0"

:: Lansare aplicatie Python
python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] A aparut o problema la pornire. Verificare dependente...
    pip install -r requirements.txt
    python main.py
    pause
)
