"""
Step 0: データ抽出スクリプト
Kizuki-Log 2.0 概念化レベル手動分析のためのデータ抽出

journals テーブルから20件ランダム抽出し、step0_data.json に出力する。
各学生 × 実習期(前半/後半) から均等にサンプリングする。
"""
import sys
import sqlite3
import json
import random
from datetime import datetime

# Windows cp932 対策
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# 再現性のためのシード固定
random.seed(42)

DB_FILE = 'kizuki_log.db'
OUTPUT_FILE = 'step0_data.json'
SAMPLE_SIZE = 20


def extract_data():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 全 journals を取得
    cursor.execute("""
        SELECT 
            j.id AS journal_id,
            j.student_id,
            j.week_number,
            j.date AS journal_date,
            j.content_raw,
            s.name AS student_name
        FROM journals j
        LEFT JOIN students s ON j.student_id = s.id
        WHERE j.content_raw IS NOT NULL AND length(j.content_raw) > 50
        ORDER BY s.name, j.week_number, j.date
    """)
    all_rows = cursor.fetchall()

    # 層化サンプリング: 学生 × 期間(前半Week1-5, 後半Week6-11) から均等に抽出
    buckets = {}
    for row in all_rows:
        name = row['student_name'] or '不明'
        period = 'early' if row['week_number'] <= 5 else 'late'
        key = f"{name}_{period}"
        if key not in buckets:
            buckets[key] = []
        buckets[key].append(row)

    # 各バケットから均等にサンプリング (20件 / 8バケット = 各2-3件)
    per_bucket = max(1, SAMPLE_SIZE // len(buckets))
    remainder = SAMPLE_SIZE - per_bucket * len(buckets)

    sampled = []
    bucket_keys = sorted(buckets.keys())
    for i, key in enumerate(bucket_keys):
        n = per_bucket + (1 if i < remainder else 0)
        bucket = buckets[key]
        random.shuffle(bucket)
        sampled.extend(bucket[:n])

    # シャッフルして提示順をランダムに
    random.shuffle(sampled)

    # feedbacks も取得
    feedback_map = {}
    cursor.execute("SELECT journal_id, comment FROM feedbacks WHERE comment IS NOT NULL")
    for fb_row in cursor.fetchall():
        feedback_map[fb_row['journal_id']] = fb_row['comment']

    # JSON構造を構築
    data = {
        "metadata": {
            "extraction_date": datetime.now().strftime("%Y-%m-%d"),
            "total_sampled": len(sampled),
            "total_journals_in_db": len(all_rows),
            "seed": 42,
            "db_file": DB_FILE,
            "sampling_method": "stratified (student x period)",
            "buckets": {k: len(v) for k, v in buckets.items()}
        },
        "entries": []
    }

    for idx, row in enumerate(sampled, 1):
        entry = {
            "id": idx,
            "journal_id": row['journal_id'],
            "context": {
                "student_name": row['student_name'] or '不明',
                "student_id": row['student_id'],
                "week_number": row['week_number'],
                "journal_date": row['journal_date'] or '',
            },
            "entry_text": row['content_raw'],
            "pharmacist_feedback": feedback_map.get(row['journal_id'], ''),
            "judgment": {
                "level": None,
                "confidence": None,
                "evidence": "",
                "notes": ""
            }
        }
        data['entries'].append(entry)

    # JSON出力
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[OK] {len(sampled)}件を抽出しました: {OUTPUT_FILE}")
    print(f"  - DB全体: {len(all_rows)}件のjournals")
    print(f"  - バケット数: {len(buckets)}")
    for key in bucket_keys:
        selected = sum(1 for e in data['entries']
                      if f"{e['context']['student_name']}_{('early' if e['context']['week_number'] <= 5 else 'late')}" == key)
        print(f"    {key}: {len(buckets[key])}件中 {selected}件を抽出")

    conn.close()


if __name__ == "__main__":
    extract_data()
