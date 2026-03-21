@echo off
chcp 65001 > nul
echo =========================================
echo  Kizuki Log: GitHub Sync (Windows)
echo =========================================

cd /d "%~dp0"

echo [1/3] Fetching latest changes from GitHub...
git pull origin main --rebase
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Failed to pull changes. Please check your internet connection or resolve merge conflicts.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [2/3] Adding local changes...
git add .
git commit -m "Auto-sync from Windows: %date% %time%"

echo.
echo [3/3] Uploading changes to GitHub...
git push origin main
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Failed to push changes.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo =========================================
echo  Sync Completed Successfully!
echo =========================================
timeout /t 3 > nul
