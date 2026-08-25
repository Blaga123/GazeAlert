@echo off
title Construire GazeAlert_Setup_v2.0.exe (Windows Installer)
color 0B
cd /d "%~dp0"

echo ============================================================
echo   PASUL 1/2: Compilare PyInstaller (GazeAlert Standalone)
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

if not exist "dist\GazeAlert\GazeAlert.exe" (
    echo.
    echo [!] Eroare la compilarea PyInstaller.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   PASUL 2/2: Generare Program Instalare (Inno Setup)
echo ============================================================
echo.

set "ISCC_PATH=C:\Users\ioanb\AppData\Local\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC_PATH%" set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%ISCC_PATH%" set "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"

"%ISCC_PATH%" gazealert_installer.iss

echo.
if exist "Output\GazeAlert_Setup_v2.0.exe" (
    echo ============================================================
    echo   [SUCCESS] KIT-UL DE INSTALARE A FOST CREAT CU SUCCES!
    echo   Fisier: Output\GazeAlert_Setup_v2.0.exe
    echo ============================================================
) else (
    echo [!] Eroare la generarea installer-ului Inno Setup.
)

echo.
pause
