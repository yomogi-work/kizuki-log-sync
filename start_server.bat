@echo off
cd /d %~dp0
echo === Kizuki-Log サーバー起動 ===
echo AI Bridge 付きサーバーを起動します...
echo Press Ctrl+C to stop the server
echo.
python start_server.py
if %errorlevel% neq 0 (
    echo.
    echo サーバーの起動に失敗しました。
    echo Pythonがインストールされているか、ポート8080が使われていないか確認してください。
    pause
)
