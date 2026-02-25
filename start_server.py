import http.server
import socketserver
import webbrowser
import os
import json
import subprocess
from datetime import datetime

# Change directory to the script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

PORT = 8080


def auto_sync_pull():
    """サーバー起動時にGitHubから最新データを取得する"""
    try:
        print("=========================================")
        print(" GitHub から最新データを取得しています...")
        print("=========================================")
        result = subprocess.run(
            ['git', 'pull', 'origin', 'main', '--rebase'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print(f"  ✓ 取得完了: {result.stdout.strip()}")
        else:
            print(f"  ⚠ 取得に失敗しました（サーバーは通常通り起動します）")
            print(f"    {result.stderr.strip()}")
    except FileNotFoundError:
        print("  ⚠ git が見つかりません。手動で同期してください。")
    except subprocess.TimeoutExpired:
        print("  ⚠ タイムアウトしました。ネットワーク接続を確認してください。")
    except Exception as e:
        print(f"  ⚠ 同期エラー: {e}")
    print()


def auto_sync_push():
    """サーバー終了時に変更をGitHubへバックアップする"""
    try:
        print()
        print("=========================================")
        print(" 変更を GitHub へバックアップしています...")
        print("=========================================")

        # ステージング
        subprocess.run(['git', 'add', '.'], capture_output=True, text=True, timeout=10)

        # コミット（変更がない場合は何もしない）
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        commit_result = subprocess.run(
            ['git', 'commit', '-m', f'Auto-sync on server shutdown: {timestamp}'],
            capture_output=True, text=True, timeout=10
        )
        if commit_result.returncode != 0 and 'nothing to commit' in commit_result.stdout:
            print("  ✓ 変更なし（バックアップ不要）")
            return

        # プッシュ
        push_result = subprocess.run(
            ['git', 'push', 'origin', 'main'],
            capture_output=True, text=True, timeout=30
        )
        if push_result.returncode == 0:
            print("  ✓ バックアップ完了!")
        else:
            print(f"  ⚠ プッシュに失敗しました")
            print(f"    {push_result.stderr.strip()}")
    except FileNotFoundError:
        print("  ⚠ git が見つかりません。手動で同期してください。")
    except subprocess.TimeoutExpired:
        print("  ⚠ タイムアウトしました。ネットワーク接続を確認してください。")
    except Exception as e:
        print(f"  ⚠ バックアップエラー: {e}")

# AI Bridge を遅延インポート（起動時のエラーを防ぐ）
ai_bridge = None

def get_ai_bridge():
    global ai_bridge
    if ai_bridge is None:
        try:
            import ai_bridge as _ai_bridge
            ai_bridge = _ai_bridge
            print("AI Bridge モジュールを読み込みました")
        except ImportError as e:
            print(f"AI Bridge の読み込みに失敗: {e}")
            return None
    return ai_bridge


class KizukiHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/save':
            self._handle_save()
        elif self.path == '/analyze':
            self._handle_analyze()
        elif self.path == '/review_weekly':
            self._handle_review_weekly()
        else:
            self.send_response(404)
            self.end_headers()

    def _handle_save(self):
        """日誌データの保存"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            data = json.loads(post_data.decode('utf-8'))
            with open('dashboard_data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
            print("Data saved successfully to dashboard_data.json")
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            print(f"Error saving data: {e}")

    def _handle_analyze(self):
        """AI解析リクエストの処理"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            request = json.loads(post_data.decode('utf-8'))

            # 必須パラメータの検証
            week = request.get('week', 1)
            log_achieved = request.get('log_achieved', '')
            log_unachieved = request.get('log_unachieved', '')
            previous_triggers = request.get('previous_triggers', '')
            instructor_notes = request.get('instructor_notes', '')

            if not log_achieved and not log_unachieved:
                self._send_json(400, {
                    "error": True,
                    "message": "日誌の内容が入力されていません。"
                })
                return

            # AI Bridge を使って解析
            bridge = get_ai_bridge()
            if bridge is None:
                self._send_json(500, {
                    "error": True,
                    "message": "AI Bridge モジュールの読み込みに失敗しました。",
                    "suggestion": "ai_bridge.py がプロジェクトフォルダに存在するか確認してください。"
                })
                return

            print(f"AI解析を開始... (Week {week})")
            
            # フロントエンドからのプロバイダ指定
            provider_override = request.get('provider', '')
            if provider_override:
                import os as _os
                _os.environ['AI_PROVIDER'] = provider_override
                print(f"  プロバイダ: {provider_override}")
            
            result = bridge.analyze_journal(
                week=week,
                log_achieved=log_achieved,
                log_unachieved=log_unachieved,
                previous_triggers=previous_triggers,
                instructor_notes=instructor_notes
            )
            print("AI解析が完了しました")

            self._send_json(200, result)

        except json.JSONDecodeError:
            self._send_json(400, {
                "error": True,
                "message": "リクエストのJSON形式が不正です。"
            })
        except Exception as e:
            print(f"Analysis error: {e}")
            self._send_json(500, {
                "error": True,
                "message": f"解析中にエラーが発生しました: {str(e)}"
            })

    def _handle_review_weekly(self):
        """週次レビューリクエストの処理"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            request = json.loads(post_data.decode('utf-8'))
            week_number = request.get('week_number')
            journals = request.get('journals', [])

            if not journals:
                self._send_json(400, {"error": True, "message": "分析対象の日誌データがありません。"})
                return

            bridge = get_ai_bridge()
            if bridge is None:
                self._send_json(500, {"error": True, "message": "AI Bridge の読み込みに失敗しました。"})
                return

            print(f"週次分析を開始... (Week {week_number})")
            
            # プロバイダ指定対応
            provider_override = request.get('provider', '')
            if provider_override:
                import os as _os
                _os.environ['AI_PROVIDER'] = provider_override

            result = bridge.analyze_weekly(week_number, journals)
            print("週次分析が完了しました")

            self._send_json(200, result)

        except Exception as e:
            print(f"Weekly review error: {e}")
            self._send_json(500, {"error": True, "message": f"週次分析中にエラーが発生しました: {str(e)}"})

    def _send_json(self, status_code, data):
        """JSONレスポンスを送信する共通メソッド"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))


try:
    # サーバー起動前にGitHubから最新データを取得
    auto_sync_pull()

    with socketserver.TCPServer(("", PORT), KizukiHandler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        webbrowser.open(f"http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
            # サーバー終了時に変更をGitHubへバックアップ
            auto_sync_push()
except OSError as e:
    if e.errno == 48 or (hasattr(e, 'winerror') and e.winerror == 10048):
        print(f"Port {PORT} is already in use. Try closing other python servers or applications.")
    else:
        print(f"Error: {e}")
