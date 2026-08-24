@echo off
chcp 65001 > nul
title GazeAlert - Sistem DIY Privire si Alerta
cls

echo ================================================================
echo        🚀 GazeAlert - DIY Python Webcam Gaze Tracker
echo ================================================================
echo.

cd /d "%~dp0"

:: 1. Verificare Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [EROARE] Python nu a fost gasit in PATH!
    echo Te rugam sa instalezi Python de la https://www.python.org/
    pause
    exit /b 1
)

:: 2. Configurare mediu virtual (venv)
if not exist "venv" (
    echo [*] Se creeaza mediul virtual Python (venv)...
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo [!] Crearea mediului virtual a esuat. Se va folosi Python global.
    )
)

:: Activare mediu virtual daca exista
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

:: 3. Instalare / Actualizare dependente
echo [*] Verificare dependente (OpenCV, MediaPipe, NumPy, Plyer)...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo [AVERTISMENT] Unele pachete au intampinat erori la instalare.
    echo Se incearca lansarea aplicatiei oricum...
)

:: 4. Rulare Aplicatie
echo.
echo [+] Lansare GazeAlert...
echo ================================================================
python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Aplicatia s-a oprit cu eroare (Cod: %ERRORLEVEL%).
    pause
)

echo.
echo [*] Aplicatia a fost oprita. O zi excelenta!
pause
