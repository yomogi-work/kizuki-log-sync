"""Phase 1: 八木 果鈴をDBに登録する"""
import sqlite3
import os

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, 'kizuki_log.db')
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # 現在のstudentsを確認
    c.execute('SELECT id, name FROM students ORDER BY id')
    existing = c.fetchall()
    print("既存の学生:")
    for row in existing:
        print(f"  ID: {row[0]}, Name: {row[1]}")
    
    # 八木がすでに存在するか確認
    c.execute("SELECT id FROM students WHERE name LIKE '%八木%'")
    yagi_exists = c.fetchone()
    
    if yagi_exists:
        print(f"\n八木さんはすでにDBに登録されています (ID: {yagi_exists[0]})")
        conn.close()
        return yagi_exists[0]
    
    # 新しいIDを決定（既存の最大ID + 3 のパターンに合わせる）
    max_id = max(row[0] for row in existing)
    new_id = max_id + 3  # 1, 4, 7, 10 -> 次は 13
    
    # 八木さんの実習開始日（dashboard_data.jsonの設定から: 2026-02-16）
    c.execute(
        'INSERT INTO students (id, name, start_date) VALUES (?, ?, ?)',
        (new_id, '八木 果鈴', '2026-02-16')
    )
    conn.commit()
    
    # 登録確認
    c.execute('SELECT id, name, start_date FROM students ORDER BY id')
    print("\n登録後の学生一覧:")
    for row in c.fetchall():
        print(f"  ID: {row[0]}, Name: {row[1]}, Start: {row[2]}")
    
    conn.close()
    print(f"\n✅ 八木 果鈴をDB ID={new_id}で登録しました")
    return new_id

if __name__ == '__main__':
    main()
