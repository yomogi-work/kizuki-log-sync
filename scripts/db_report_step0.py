import sqlite3
import json

conn = sqlite3.connect('kizuki_log.db')
cursor = conn.cursor()

print("=" * 60)
print("[DB構造報告]")
print("=" * 60)

# テーブル一覧
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
tables = [r[0] for r in cursor.fetchall()]
print(f"\n- テーブル: {', '.join(tables)}")

# insights テーブル構造
cursor.execute("PRAGMA table_info(insights);")
cols = cursor.fetchall()
print(f"\n- insights カラム:")
for c in cols:
    print(f"    {c[1]} ({c[2]}), PK={c[5]}, NOT NULL={c[3]}")

# journals テーブル構造
cursor.execute("PRAGMA table_info(journals);")
cols = cursor.fetchall()
print(f"\n- journals カラム:")
for c in cols:
    print(f"    {c[1]} ({c[2]}), PK={c[5]}, NOT NULL={c[3]}")

# students テーブル構造
cursor.execute("PRAGMA table_info(students);")
cols = cursor.fetchall()
print(f"\n- students カラム:")
for c in cols:
    print(f"    {c[1]} ({c[2]}), PK={c[5]}, NOT NULL={c[3]}")

# データ件数
cursor.execute("SELECT COUNT(*) FROM insights;")
insights_count = cursor.fetchone()[0]
print(f"\n- insights件数: {insights_count}件")

cursor.execute("SELECT COUNT(DISTINCT s.id) FROM students s;")
student_count = cursor.fetchone()[0]
print(f"- 学生数: {student_count}名")

cursor.execute("SELECT COUNT(DISTINCT j.week_number) FROM journals j;")
week_count = cursor.fetchone()[0]
print(f"- Week数: {week_count}週分")

# Type分布
cursor.execute("SELECT type, COUNT(*) as cnt FROM insights GROUP BY type ORDER BY cnt DESC;")
print(f"\n- Type分布:")
for row in cursor.fetchall():
    print(f"    {row[0]}: {row[1]}件")

# insights → journals の参照
cursor.execute("""
SELECT i.id, i.journal_id, j.student_id, j.week_number, j.content_raw
FROM insights i
LEFT JOIN journals j ON i.journal_id = j.id
LIMIT 3;
""")
print(f"\n- insights → journals 参照方法:")
print(f"    insights.journal_id → journals.id (FOREIGN KEY)")
sample = cursor.fetchall()
for s in sample:
    content_preview = (s[4] or '')[:80]
    print(f"    例: insight#{s[0]} → journal#{s[1]} (student={s[2]}, week={s[3]})")
    print(f"         content_raw: {content_preview}...")

# 全学生×全Week のデータ有無
cursor.execute("""
SELECT s.name, j.week_number, COUNT(i.id) as insight_count
FROM students s
LEFT JOIN journals j ON s.id = j.student_id
LEFT JOIN insights i ON j.id = i.journal_id
GROUP BY s.name, j.week_number
ORDER BY s.name, j.week_number;
""")
print(f"\n- 学生 × Week × Insight件数:")
for row in cursor.fetchall():
    print(f"    {row[0]} / Week {row[1]}: {row[2]}件")

conn.close()
