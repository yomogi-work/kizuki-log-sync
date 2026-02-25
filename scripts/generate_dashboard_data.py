import sqlite3
import json
import os

def generate_json_data(db_path, output_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Students
    cursor.execute('SELECT * FROM students')
    students = [dict(row) for row in cursor.fetchall()]
    
    data = {"students": []}
    
    for s in students:
        s_id = s["id"]
        s_name = s["name"]
        
        # 2. Journals & Feedbacks
        cursor.execute('''
            SELECT j.id, j.date, j.week_number, j.content_raw, f.comment as feedback 
            FROM journals j
            LEFT JOIN feedbacks f ON j.id = f.journal_id
            WHERE j.student_id = ?
            ORDER BY j.date ASC
        ''', (s_id,))
        journals = [dict(row) for row in cursor.fetchall()]
        
        # 3. Insights
        cursor.execute('''
            SELECT i.journal_id, i.type, i.snippet, i.reason 
            FROM insights i
            JOIN journals j ON i.journal_id = j.id
            WHERE j.student_id = ?
        ''', (s_id,))
        insights = [dict(row) for row in cursor.fetchall()]
        
        # 4. Growth Triggers
        cursor.execute('''
            SELECT date, description FROM growth_triggers WHERE student_id = ? ORDER BY date ASC
        ''', (s_id,))
        growth_triggers = [dict(row) for row in cursor.fetchall()]
        
        data["students"].append({
            "id": s_id,
            "name": s_name,
            "journals": journals,
            "insights": insights,
            "growth_triggers": growth_triggers
        })

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    conn.close()
    print(f"Dashboard data generated at {output_path}")

if __name__ == "__main__":
    base_dir = "/Users/yomogiyakkyoku/Library/CloudStorage/OneDrive-株式会社ｗｏｒｍｗｏｏｄ/実習ツール類/Kizuki log"
    db_path = os.path.join(base_dir, "kizuki_log.db")
    output_path = os.path.join(base_dir, "dashboard_data.json")
    generate_json_data(db_path, output_path)
