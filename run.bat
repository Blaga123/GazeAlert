@echo off
chcp 65001 > nul
title GazeAlert AI Suite
cls

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
