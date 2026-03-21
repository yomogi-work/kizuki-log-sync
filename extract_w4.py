import json

with open('dashboard_data.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

yagi = next((s for s in d['students'] if s['name'] == '八木 果鈴'), None)
if yagi:
    w4 = [j for j in yagi['journals'] if j.get('week_number') == 4]
    with open('w4.txt', 'w', encoding='utf-8') as out:
        for j in w4:
            out.write(f"--- 日付: {j.get('date')} ---\n")
            out.write(f"[実習内容]\n{j.get('practical_content', '')}\n")
            out.write(f"[反省]\n{j.get('unachieved_point', '')}\n")
            out.write(f"[メモ]\n{j.get('instructor_notes', '')}\n")
            out.write(f"[FB]\n{j.get('feedback', '')}\n\n")
