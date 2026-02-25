#!/bin/bash
# ──────────────────────────────────────
# Kizuki-Log サーバー起動スクリプト (Mac)
# ダブルクリックで起動できます
# ──────────────────────────────────────

# スクリプトのあるディレクトリに移動
cd "$(dirname "$0")"

echo "=== Kizuki-Log サーバー起動 ==="
echo ""

# ポートが既に使用中なら解放を試みる
PORT=8080
if lsof -i :$PORT -t >/dev/null 2>&1; then
    echo "⚠️  ポート $PORT が使用中です。既存プロセスを停止します..."
    kill $(lsof -i :$PORT -t) 2>/dev/null
    sleep 1
    echo "✅ 既存プロセスを停止しました"
fi

# python3 の存在確認
if ! command -v python3 &>/dev/null; then
    echo "❌ エラー: python3 が見つかりません"
    echo "Python 3 をインストールしてください: https://www.python.org/downloads/"
    echo ""
    echo "何かキーを押すと終了します..."
    read -n 1
    exit 1
fi

echo "🐍 Python: $(python3 --version)"
echo "📂 作業ディレクトリ: $(pwd)"
echo "🌐 ブラウザで http://localhost:$PORT が開きます"
echo ""
echo "サーバーを停止するには Ctrl+C を押してください"
echo "────────────────────────────────────"
echo ""

# サーバー起動
python3 start_server.py

# エラーで終了した場合、ウィンドウを閉じないようにする
echo ""
echo "サーバーが停止しました。"
echo "何かキーを押すと終了します..."
read -n 1
