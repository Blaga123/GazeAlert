@echo off
title Push GitHub Profile README to Blaga123/Blaga123
echo ============================================================
echo   Incarcare Profil GitHub Personalizat (Blaga123/Blaga123)
echo ============================================================
echo.
echo Asigura-te ca ai creat depozitul "Blaga123" pe https://github.com/new
echo.
pause
cd /d "E:\Blaga123"
git remote set-url origin https://github.com/Blaga123/Blaga123.git
git push -u origin main --force
echo.
echo ============================================================
echo   [+] GATA! Profilul tau GitHub a fost actualizat!
echo ============================================================
pause
