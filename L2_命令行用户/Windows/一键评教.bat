@echo off
rem ============================================================
rem  PJ Auto Eval - Windows launcher (L2)
rem  This file is intentionally PURE ASCII so that it parses
rem  correctly on ANY Windows locale (cp936 / cp437 / cp1252 ...).
rem  All Chinese output is produced by launcher.py, which switches
rem  the console to UTF-8 by itself.
rem  Do NOT save this file with non-ASCII characters.
rem ============================================================
setlocal
cd /d "%~dp0"
title PJ Auto Eval
chcp 65001 >nul 2>&1

set "PY="
python -c "import sys" >nul 2>&1
if not errorlevel 1 set "PY=python"
if defined PY goto RUN

py -3 -c "import sys" >nul 2>&1
if not errorlevel 1 set "PY=py -3"
if defined PY goto RUN

echo.
echo   [ERROR] Python 3 not found.
echo.
echo   Install it from: https://www.python.org/downloads/
echo   During setup, CHECK the box "Add python.exe to PATH".
echo.
pause
exit /b 1

:RUN
%PY% launcher.py
set "RC=%ERRORLEVEL%"
if "%RC%"=="0" goto DONE
echo.
echo   [Exit code %RC%] See the messages above.
:DONE
echo.
pause
exit /b 0
