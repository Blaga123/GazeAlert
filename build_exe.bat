@echo off
title Construire GazeAlert.exe (Standalone Windows App)
color 0A
cd /d "%~dp0"

echo ============================================================
echo   Generare GazeAlert.exe - Standalone Executable
echo ============================================================
echo.

python -m PyInstaller --noconfirm --onedir --windowed ^
    --name "GazeAlert" ^
    --icon "app_icon.ico" ^
    --add-data "sounds;sounds" ^
    --add-data "face_landmarker.task;." ^
    --add-data "config.json;." ^
    --add-data "calibration_matrix.json;." ^
    --add-data "app_icon.ico;." ^
    --hidden-import "plyer.platforms.win.notification" ^
    --hidden-import "pystray._win32" ^
    --hidden-import "win10toast" ^
    main.py

echo.
if exist "dist\GazeAlert\GazeAlert.exe" (
    echo ============================================================
    echo   [SUCCESS] Executabilul a fost creat cu succes!
    echo   Locatie: dist\GazeAlert\GazeAlert.exe
    echo ============================================================
) else (
    echo [!] A aparut o eroare la compilare.
)

echo.
pause
