---
description: ファイルやスクリプトを作成・配置する際の運用ルール
---

# Kizuki-Log ファイル運用ルール

小規模薬局のシステムを持続可能に保つため、整理されたフォルダ構造と命名規則に従って開発を行うこと。

## 1. フォルダ構造と配置ルール

| 種類 | 配置場所 | 命名規則・内容 |
|------|---------|-------------|
| **メインUI & コア** | `/` (ルート) | `index.html`, `app.js`, `style.css`, `start_server.py`, `ai_bridge.py` |
| **運用データ** | `/` (ルート) | `dashboard_data.json`, `kizuki_log.db` |
| **ドキュメント** | `docs/` | 仕様書や設計書など (`*.md`, `*.txt`) |
| **Step 0関連** | `step0/` | 研究判定用など、Step0に特化したファイル (`step0_*`) |
| **DB操作スクリプト** | `scripts/db/` | DB初期化やマイグレーション用 (`init_db.py`, `migrate_db.py` など動詞+名詞) |
| **データ処理スクリプト**| `scripts/data/` | JSONやPDFのインポート・処理用 (`import_*.py`, `generate_*.py`) |
| **ユーティリティ** | `scripts/utils/` | 各種リスト化、確認用 (`list_*.py`, `merge_*.py`) |
| **同期用バッチ** | `sync/` | Windows/Mac別の手動同期スクリプト (`sync_*.bat`, `sync_*.command`) |
| **一次デバッグ・検証**| `archive/` 以下 | コミット不要な使い捨てスクリプト、レポート、ログ出力などは全てここへ。 |

## 2. 開発時の必須アクション

1. **新規機能の追加時**: 原則として既存のファイル（`index.html`, `app.js`, `start_server.py`）を拡張すること。無闇にルート直下にファイルを増やさない。
2. **スクリプト作成時**: 1回限りの確認・デバッグ用スクリプト（例: `check_foo.py`）は、最初から `archive/debug_scripts/` に作成すること。
3. **データ出力時**: デバッグ目的の JSON/TXT バックアップなどは、必ず `archive/reports/` または `archive/data_snapshots/` に出力すること。

## 3. Git連携のルール

- `start_server.py` は起動時に `git pull`、終了時に `git push` を自動実行する。
- サーバーをローカルで終了する際は、必ず提供されている「終了ボタン（/shutdown）」を利用し、Gracefulに行うこと。
- `archive/` フォルダ以下は `.gitignore` に指定されており、版管理から除外されている。
