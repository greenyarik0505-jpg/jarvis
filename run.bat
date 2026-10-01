@echo off
title J.A.R.V.I.S. Desktop & Voice Agent
cd /d "%~dp0"
python main.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo [JARVIS] Execution stopped with error code %ERRORLEVEL%.
    pause
)
