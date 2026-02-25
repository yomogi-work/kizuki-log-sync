#!/bin/bash
# ──────────────────────────────────────
# Kizuki-Log サーバー起動スクリプト (Mac)
# ダブルクリックで起動できます
# ──────────────────────────────────────

# スクリプトのあるディレクトリに移動（日本語パス対応）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || {
    echo "❌ エラー: プロジェクトフォルダへ移動できません"
    echo "パス: $SCRIPT_DIR"
    echo ""
    echo "何かキーを押すと終了します..."
    read -n 1
    exit 1
}

echo "=== Kizuki-Log サーバー起動 ==="
echo ""

# ポートが既に使用中なら解放を試みる
PORT=8080
if lsof -i :$PORT -t >/dev/null 2>&1; then
    echo "⚠️  ポート $PORT が使用中です。既存プロセスを停止します..."
    kill $(lsof -i :$PORT -t) 2>/dev/null
    sleep 2
    if lsof -i :$PORT -t >/dev/null 2>&1; then
        echo "⚠️  まだ停止していません。強制停止を試みます..."
        kill -9 $(lsof -i :$PORT -t) 2>/dev/null
        sleep 1
    fi
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

# .venv があれば自動的にアクティベート
if [ -d ".venv" ] && [ -f ".venv/bin/activate" ]; then
    echo "📦 仮想環境を検出しました。アクティベートします..."
    source .venv/bin/activate
fi

# 必須ファイルの存在確認
MISSING_FILES=""
for f in start_server.py index.html app.js style.css; do
    if [ ! -f "$f" ]; then
        MISSING_FILES="$MISSING_FILES  - $f\n"
    fi
done

if [ -n "$MISSING_FILES" ]; then
    echo "❌ エラー: 以下の必須ファイルが見つかりません:"
    echo -e "$MISSING_FILES"
    echo "プロジェクトフォルダの内容を確認してください。"
    echo ""
    echo "何かキーを押すと終了します..."
    read -n 1
    exit 1
fi

# .env ファイルの確認
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "⚠️  .env ファイルがありません。.env.example を元に作成してください。"
        echo "   cp .env.example .env"
        echo ""
    fi
fi

echo "🐍 Python: $(python3 --version)"
echo "📂 作業ディレクトリ: $(pwd)"
echo "🌐 ブラウザで http://localhost:$PORT が開きます"
echo ""
echo "サーバーを停止するには Ctrl+C を押すか、"
echo "このウィンドウを閉じてください。"
echo "────────────────────────────────────"
echo ""

# サーバー起動
python3 start_server.py

# エラーで終了した場合、ウィンドウを閉じないようにする
EXIT_CODE=$?
echo ""
if [ $EXIT_CODE -ne 0 ]; then
    echo "❌ サーバーがエラーで停止しました (終了コード: $EXIT_CODE)"
else
    echo "サーバーが停止しました。"
fi
echo "何かキーを押すと終了します..."
read -n 1
