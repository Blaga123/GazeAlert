@echo off
title Incarcare GazeAlert pe GitHub
color 0A
cd /d "E:\GazeAlert"

echo ============================================================
echo   Incarcare Proiect GazeAlert pe GitHub (Blaga123/GazeAlert)
echo ============================================================
echo.

git config user.name "Blaga Ioan Catalin"
git config user.email "blaga.ioan-catalin.24@stud.umfst.ro"
git remote remove origin 2>nul
git remote add origin https://github.com/Blaga123/GazeAlert.git
git branch -M main

echo [*] Trimitere fisiere, cod complet si README pe GitHub...
echo (Daca apare fereastra de autentificare, apasa 'Sign in with your browser')
echo.

git push -u origin main --force

echo.
if %errorlevel% equ 0 (
    echo ============================================================
    echo   [SUCCESS] Proiectul a fost incarcat cu succes pe GitHub!
    echo   Viziteaza: https://github.com/Blaga123/GazeAlert
    echo ============================================================
) else (
    echo [!] A aparut o eroare la trimitere. Asigura-te ca esti conectat la GitHub.
)

echo.
pause
