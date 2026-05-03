@echo off
title Melvin Desktop Assistant

:: Pfade definieren
set VENV=%~dp0..\..venv\Scripts\activate.bat
set PROJECT=%~dp0
set UI=%~dp0melvin-ui

echo ========================================
echo   M.E.L.V.I.N - Desktop Assistant
echo ========================================
echo.

:: Electron UI im Hintergrund starten
echo [1/2] Starte Melvin UI...
start "Melvin UI" cmd /c "cd /d %UI% && npm start"

:: Kurz warten damit UI sich initialisieren kann
timeout /t 3 /nobreak >nul

:: Python Backend starten
echo [2/2] Starte Melvin Backend...
call D:\Dokumente\Final\.venv\Scripts\activate.bat
cd /d %PROJECT%
python main.py

:: Falls Python beendet wird, alles schließen
echo.
echo Melvin wurde beendet.
pause