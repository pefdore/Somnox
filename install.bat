@echo off
chcp 65001 >nul
title Somnox - Installation
echo === Installation de Somnox ===
echo.

where winget >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] winget indisponible. Installez "App Installer" depuis le Microsoft Store,
    echo     ou installez Python manuellement : https://www.python.org/downloads/
    pause
    exit /b 1
)

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [..] Python absent - installation via winget...
    winget install --id Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements
    echo.
    echo [i] Python vient d'etre installe : FERMEZ cette fenetre, rouvez-la (chemin D:\Somnox)
    echo    puis relancez install.bat pour continuer.
    pause
    exit /b 0
)

echo [OK] Python detecte.
echo [..] Installation des dependances...
python -m pip install -r requirements.txt || goto :fail
python -m pip install -e . || goto :fail

echo.
echo [..] Installation de Tesseract OCR (pack fra)...
python -m somnox.cli setup

echo.
echo === Installation terminee ===
echo Lancez l'application avec :  somnox gui
echo (si non reconnu, fermez puis rouvrez le terminal)
pause
exit /b 0

:fail
echo [!] Echec de l'installation. Verifiez le message d'erreur ci-dessus.
pause
exit /b 1
