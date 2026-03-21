"""Phase 2: dashboard_data.jsonの八木データを修復する
- Date.now() IDをDB ID (13)に差し替え
- repair_bakからジャーナルデータを救出してマージ
- settings情報は保持
"""
import json
import os
import shutil
from datetime import datetime

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(base_dir, 'dashboard_data.json')
    repair_bak_path = os.path.join(base_dir, 'dashboard_data.json.repair_bak')
    
    DB_YAGI_ID = 13  # Phase 1で登録したID
    
    # === 現在のJSONを読み込み ===
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # === repair_bakからジャーナルを救出 ===
    rescued_journals = []
    if os.path.exists(repair_bak_path):
        with open(repair_bak_path, 'r', encoding='utf-8') as f:
            bak_data = json.load(f)
        yagi_bak = next((s for s in bak_data.get('students', []) if '八木' in s.get('name', '')), None)
        if yagi_bak and yagi_bak.get('journals'):
            rescued_journals = yagi_bak['journals']
            print(f"✅ repair_bakから{len(rescued_journals)}件のジャーナルを救出")
            for j in rescued_journals:
                print(f"   Date: {j.get('date')}")
    
    # === 現在のJSONの八木データを修正 ===
    yagi = next((s for s in data['students'] if '八木' in s.get('name', '')), None)
    
    if not yagi:
        print("❌ dashboard_data.jsonに八木さんが見つかりません")
        return
    
    old_id = yagi['id']
    print(f"\n八木さんのID変更: {old_id} → {DB_YAGI_ID}")
    
    # IDを差し替え
    yagi['id'] = DB_YAGI_ID
    
    # ジャーナルのマージ（既存 + 救出分）
    existing_dates = {j.get('date') for j in yagi.get('journals', [])}
    merged_count = 0
    for rescued_j in rescued_journals:
        if rescued_j.get('date') not in existing_dates:
            yagi['journals'].append(rescued_j)
            merged_count += 1
    
    print(f"ジャーナルマージ: 既存{len(existing_dates)}件 + 救出{merged_count}件 = 合計{len(yagi['journals'])}件")
    
    # settings情報は保持（確認表示）
    if yagi.get('settings'):
        s = yagi['settings']
        print(f"Settings保持: {s.get('startDate')} ~ {s.get('endDate')}")
    
    # === バックアップを作成してから保存 ===
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(base_dir, f'dashboard_data.json.pre_fix_{timestamp}')
    shutil.copy2(json_path, backup_path)
    print(f"\n修正前バックアップ: {os.path.basename(backup_path)}")
    
    # 保存
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ dashboard_data.json を修復しました！")
    
    # === 修復確認 ===
    with open(json_path, 'r', encoding='utf-8') as f:
        verify = json.load(f)
    yagi_verify = next((s for s in verify['students'] if '八木' in s.get('name', '')), None)
    print(f"\n=== 修復確認 ===")
    print(f"  Name: {yagi_verify['name']}")
    print(f"  ID: {yagi_verify['id']}")
    print(f"  Journals: {len(yagi_verify.get('journals', []))}")
    for j in yagi_verify.get('journals', []):
        print(f"    Date: {j.get('date')}")

if __name__ == '__main__':
    main()
