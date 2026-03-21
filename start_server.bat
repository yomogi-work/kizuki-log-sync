@echo off
chcp 65001 > nul
cd /d %~dp0
echo =========================================
echo   Kizuki-Log サーバー起動
echo =========================================
echo.
echo Git Pull/Push は自動で実行されます。
echo 終了はブラウザの「システム終了」ボタンから。
echo.
python start_server.py
if %errorlevel% neq 0 (
    echo.
    echo サーバーの起動に失敗しました。
    echo Pythonがインストールされているか確認してください。
    pause
)
