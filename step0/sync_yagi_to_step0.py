"""
dashboard_data.json の特定の学生（八木さん）のデータを読み込み、
Step 0の判定用データファイル（step0_data.json または step0_judged_*.json）に同期するスクリプト。

日々の実習後、指導者がこのスクリプトを実行することで、
最新の日誌データを判定画面（step0_interface.html）に流し込むことができます。
"""
import sys
import json
import os
import glob
from datetime import datetime

# Windows cp932 対策
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

TARGET_STUDENT_NAME = "八木"
DASHBOARD_FILE = "dashboard_data.json"


def get_latest_step0_file():
    """最後に作成・更新されたStep0データファイルを探す"""
    judged_files = sorted(glob.glob('step0_judged_*.json'))
    if judged_files:
        return judged_files[-1]
    
    if os.path.exists('step0_data.json'):
        return 'step0_data.json'
        
    return None


def calculate_week_number(start_date_str, journal_date_str):
    """開始日と日誌の日付から、第何週目かを計算する"""
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        journal_date = datetime.strptime(journal_date_str, "%Y-%m-%d").date()
        days_diff = (journal_date - start_date).days
        if days_diff < 0:
            return 1
        return (days_diff // 7) + 1
    except ValueError:
        return 1


def sync_data():
    print(f"[INFO] '{TARGET_STUDENT_NAME}' さんの日誌データを同期します...")
    
    # 1. Dashboard データの読み込み
    if not os.path.exists(DASHBOARD_FILE):
        print(f"[ERROR] {DASHBOARD_FILE} が見つかりません。")
        sys.exit(1)
        
    with open(DASHBOARD_FILE, 'r', encoding='utf-8') as f:
        dashboard_data = json.load(f)
        
    # 対象学生を探す
    student = next((s for s in dashboard_data.get('students', []) if TARGET_STUDENT_NAME in s.get('name', '')), None)
    if not student:
        print(f"[ERROR] {DASHBOARD_FILE} の中に '{TARGET_STUDENT_NAME}' さんが見つかりません。")
        sys.exit(1)
        
    journals = student.get('journals', [])
    if not journals:
        print(f"[INFO] '{TARGET_STUDENT_NAME}' さんの日誌データはまだありません。")
        sys.exit(0)
        
    start_date = student.get('startDate', '2026-02-16') # フォールバック
        
    # 2. 既存の Step0 データの読み込み
    step0_file = get_latest_step0_file()
    if not step0_file:
        print("[WARN] step0_data.json や step0_judged_*.json が見つかりません。新規作成します。")
        step0_data = {
            "metadata": {
                "sync_date": datetime.now().strftime("%Y-%m-%d"),
                "note": "Auto-synced from dashboard_data.json"
            },
            "entries": []
        }
        step0_file = "step0_data.json"
    else:
        print(f"[INFO] 既存の判定ファイル '{step0_file}' を読み込みます。")
        with open(step0_file, 'r', encoding='utf-8') as f:
            step0_data = json.load(f)
            
    # Step0 に既に存在する日誌の日付リストを作成
    existing_dates = []
    for entry in step0_data.get('entries', []):
        if TARGET_STUDENT_NAME in entry.get('context', {}).get('student_name', ''):
            existing_dates.append(entry.get('context', {}).get('journal_date', ''))
            
    # 3. 新しい日誌を追加
    added_count = 0
    max_id = max([e.get('id', 0) for e in step0_data.get('entries', [])] + [0])
    
    for journal in journals:
        j_date = journal.get('date')
        if not j_date:
            continue
            
        # すでに追加済みの場合はスキップ
        if j_date in existing_dates:
            continue
            
        # 空の日誌はスキップ
        practical = journal.get('practical_content', '').strip()
        unachieved = journal.get('unachieved_point', '').strip()
        if not practical and not unachieved:
            continue
            
        max_id += 1
        week_num = calculate_week_number(start_date, j_date)
        
        # 結合して1つのテキストにする
        content_raw = f"【具体的な実習内容】\n{practical}\n\n【達成できなかった点・反省】\n{unachieved}"
        
        new_entry = {
            "id": max_id,
            "journal_id": f"{student.get('id', 'unknown')}_{j_date}",
            "context": {
                "student_name": student.get('name', TARGET_STUDENT_NAME),
                "student_id": student.get('id'),
                "week_number": week_num,
                "journal_date": j_date
            },
            "entry_text": content_raw,
            "pharmacist_feedback": journal.get('instructor_notes', ''),
            "judgment": {
                "level": None,
                "concept_source": None,
                "confidence": None,
                "evidence": "",
                "notes": ""
            }
        }
        step0_data['entries'].append(new_entry)
        added_count += 1
        print(f"  -> 追加: {j_date} (Week {week_num})")
        
    # 4. 保存
    if added_count > 0:
        # 毎回新しい step0_data.json に上書き保存する（judged_*.json はUI側で出力されるため）
        with open('step0_data.json', 'w', encoding='utf-8') as f:
            json.dump(step0_data, f, ensure_ascii=False, indent=2)
        print(f"\n[OK] {added_count} 件の新しい日誌を 'step0_data.json' に追加しました。")
    else:
        print("\n[INFO] 追加すべき新しい日誌はありませんでした（すべて同期済みです）。")

if __name__ == "__main__":
    sync_data()
