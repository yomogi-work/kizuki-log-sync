@echo off
cd /d %~dp0
echo =========================================
echo   Kizuki-Log Server Starting...
echo =========================================
echo.
echo Git Pull/Push is automated by the Python script.
echo To shutdown, use the "Shutdown" button in the browser.
echo.
python start_server.py
if %errorlevel% neq 0 (
    echo.
    echo Failed to start the server.
    echo Please ensure Python is installed.
    pause
)
