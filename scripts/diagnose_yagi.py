"""八木さんのデータ同期問題の包括的診断スクリプト"""
import json
import sqlite3
import os

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # === 1. dashboard_data.json の八木データ ===
    print("=" * 60)
    print("1. dashboard_data.json の八木データ")
    print("=" * 60)
    json_path = os.path.join(base_dir, 'dashboard_data.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for s in data.get('students', []):
        print(f"  Student: {s['name']} | ID: {s['id']} | Journals: {len(s.get('journals', []))}")
    
    yagi = next((s for s in data['students'] if '八木' in s.get('name', '')), None)
    if yagi:
        print(f"\n  八木さん詳細:")
        print(f"    ID: {yagi['id']}")
        print(f"    Name: {yagi['name']}")
        print(f"    Journals count: {len(yagi.get('journals', []))}")
        print(f"    Growth triggers: {yagi.get('growth_triggers', [])}")
        print(f"    Insights: {yagi.get('insights', [])}")
        print(f"    All keys: {list(yagi.keys())}")
        
        # settings check
        if 'settings' in yagi:
            print(f"    Settings: {yagi['settings']}")
    else:
        print("  八木さんが見つかりません")
    
    # === 2. バックアップJSONの八木データ ===
    print("\n" + "=" * 60)
    print("2. バックアップファイルの八木データ")
    print("=" * 60)
    for bak_name in ['dashboard_data.json.bak', 'dashboard_data.json.repair_bak']:
        bak_path = os.path.join(base_dir, bak_name)
        if os.path.exists(bak_path):
            try:
                with open(bak_path, 'r', encoding='utf-8') as f:
                    bak_data = json.load(f)
                yagi_bak = next((s for s in bak_data.get('students', []) if '八木' in s.get('name', '')), None)
                if yagi_bak:
                    journals = yagi_bak.get('journals', [])
                    print(f"  {bak_name}: ID={yagi_bak['id']}, Journals={len(journals)}")
                    if journals:
                        for j in journals[:3]:
                            pc = j.get('practical_content', '') or ''
                            up = j.get('unachieved_point', '') or ''
                            print(f"    Date: {j.get('date')} | Practical: {len(pc)} chars | Unachieved: {len(up)} chars")
                        if len(journals) > 3:
                            print(f"    ... and {len(journals)-3} more")
                else:
                    print(f"  {bak_name}: 八木さんなし")
            except Exception as e:
                print(f"  {bak_name}: エラー - {e}")
        else:
            print(f"  {bak_name}: ファイルなし")
    
    # === 3. kizuki_log.db の八木データ ===
    print("\n" + "=" * 60)
    print("3. kizuki_log.db の八木データ")
    print("=" * 60)
    db_path = os.path.join(base_dir, 'kizuki_log.db')
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # テーブル一覧
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in c.fetchall()]
        print(f"  テーブル一覧: {tables}")
        
        # 各テーブルのスキーマ
        for table in tables:
            c.execute(f"PRAGMA table_info({table})")
            cols = [(r[1], r[2]) for r in c.fetchall()]
            c.execute(f"SELECT COUNT(*) FROM {table}")
            count = c.fetchone()[0]
            print(f"\n  {table}: {count} rows, columns: {cols}")
        
        # 八木関連データを検索
        for table in tables:
            c.execute(f"PRAGMA table_info({table})")
            cols = [r[1] for r in c.fetchall()]
            for col in cols:
                try:
                    c.execute(f"SELECT * FROM {table} WHERE {col} LIKE '%八木%' LIMIT 5")
                    rows = c.fetchall()
                    if rows:
                        print(f"\n  {table}.{col} に '八木' を発見:")
                        for row in rows:
                            print(f"    {row}")
                except:
                    pass
        
        conn.close()
    else:
        print("  kizuki_log.db が見つかりません")
    
    # === 4. app.js の保存ロジック確認 ===
    print("\n" + "=" * 60)
    print("4. データ同期に関する考察")
    print("=" * 60)
    print("  - 八木さんのID (1770859069060) はDate.now()由来の可能性大")
    print("  - 他の学生のID (1,4,7,10) はDBの連番ID")
    print("  - → 八木さんはDBから読み込まれず、UIから新規追加された可能性")
    print("  - ジャーナルが0 → データがどこかで失われた")

if __name__ == '__main__':
    main()
