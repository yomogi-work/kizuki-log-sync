"""
全44 PDFから日誌データを抽出し、kizuki_log.db に投入するスクリプト
Step 0 の前処理として、全週報を DB に格納する。
"""
import os
import re
import sys
import json
import sqlite3
import glob
import datetime
from PyPDF2 import PdfReader

# Windows cp932 対策
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

RAW_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'raw_data')
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'kizuki_log.db')
EXTRACTED_TEXT_FILE = os.path.join(RAW_DATA_DIR, 'extracted_text_all.txt')


def extract_text_from_pdfs():
    """全PDFからテキストを抽出し、extracted_text_all.txt に出力"""
    pdf_files = sorted(glob.glob(os.path.join(RAW_DATA_DIR, '日誌_*.pdf')))
    print(f"[PDF] {len(pdf_files)} 個のPDFを検出")

    all_text = []
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        print(f"  処理中: {filename}")
        try:
            reader = PdfReader(pdf_path)
            file_text = f"--- File: {filename} ---\n"
            for i, page in enumerate(reader.pages, 1):
                text = page.extract_text() or ""
                file_text += f"-- Page {i} --\n{text}\n"
            file_text += "\n==================================================\n\n"
            all_text.append(file_text)
        except Exception as e:
            print(f"  [WARN] エラー: {filename} - {e}")

    with open(EXTRACTED_TEXT_FILE, 'w', encoding='utf-8') as f:
        f.write(''.join(all_text))

    print(f"[OK] テキスト抽出完了: {EXTRACTED_TEXT_FILE}")
    return EXTRACTED_TEXT_FILE


def parse_date(date_str, year):
    """MM月DD日 形式の日付をパース"""
    try:
        match = re.search(r'(\d+)月(\d+)日', date_str)
        if match:
            month = int(match.group(1))
            day = int(match.group(2))
            return f"{year}-{month:02d}-{day:02d}"
    except Exception as e:
        print(f"  [WARN] 日付パースエラー: {date_str} - {e}")
    return None


def parse_extracted_text(text_file):
    """抽出テキストを解析し、学生ごとの日誌データを構造化"""
    with open(text_file, 'r', encoding='utf-8') as f:
        content = f.read()

    files = re.split(r'--- File: (.*?) ---', content)[1:]
    students_data = {}

    for i in range(0, len(files), 2):
        filename = files[i]
        file_content = files[i + 1]

        # ファイル名から年を抽出
        year_match = re.search(r'_(\d{4})\d{4}\.pdf', filename)
        year = year_match.group(1) if year_match else "2025"

        # ファイル名から学生名を抽出
        name_from_file = re.search(r'日誌_(.+?)_\d+_', filename)
        student_name_hint = name_from_file.group(1).replace("　", " ").strip() if name_from_file else None

        pages = re.split(r'-- Page \d+ --', file_content)

        for page in pages:
            if not page.strip():
                continue

            # 学生名を抽出
            name_match = re.search(r'氏名\(\s*(.*?)\s*\)', page)
            if not name_match:
                continue
            name = name_match.group(1).replace("　", " ").strip()

            # 日付を抽出
            date_match = re.search(r'日誌 (\d+月\d+日)', page)
            if not date_match:
                continue
            formatted_date = parse_date(date_match.group(1), year)
            if not formatted_date:
                continue

            # 学生データ初期化
            if name not in students_data:
                students_data[name] = {}

            # 日付ごとのエントリ初期化
            if formatted_date not in students_data[name]:
                students_data[name][formatted_date] = {
                    "practical_content": "",
                    "unachieved_point": "",
                    "pharmacist_comment": ""
                }

            entry = students_data[name][formatted_date]

            # 具体的な実習内容
            practical_match = re.search(
                r'具体的な実習内容\s*(.*?)(?=実習に関する能力|実習にて達成できなかった点|-- Page|==+|$)',
                page, re.DOTALL
            )
            if practical_match:
                text = practical_match.group(1).strip()
                if text and len(text) > 5:
                    if entry["practical_content"]:
                        entry["practical_content"] += "\n" + text
                    else:
                        entry["practical_content"] = text

            # 実習にて達成できなかった点
            unachieved_match = re.search(
                r'実習にて達成できなかった点\s*\n?\s*(?:（次回への反省・改善点）)?\s*(.*?)(?=添付資料|薬剤師のコメント|-- Page|==+|$)',
                page, re.DOTALL
            )
            if unachieved_match:
                text = unachieved_match.group(1).strip()
                if text and len(text) > 3:
                    if entry["unachieved_point"]:
                        entry["unachieved_point"] += "\n" + text
                    else:
                        entry["unachieved_point"] = text

            # 薬剤師のコメント
            comment_match = re.search(
                r'薬剤師のコメント\s*(.*?)(?=登録者|添付資料|-- Page|==+|$)',
                page, re.DOTALL
            )
            if comment_match:
                text = comment_match.group(1).strip()
                if text and len(text) > 2:
                    if entry["pharmacist_comment"]:
                        entry["pharmacist_comment"] += "\n" + text
                    else:
                        entry["pharmacist_comment"] = text

    return students_data


def calculate_week_number(entry_date_str, start_date_str):
    """開始日からの週数を計算"""
    entry_date = datetime.datetime.strptime(entry_date_str, "%Y-%m-%d")
    start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
    days_diff = (entry_date - start_date).days
    if days_diff < 0:
        return 1
    return (days_diff // 7) + 1


def ingest_to_db(students_data):
    """パース結果を kizuki_log.db に投入"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 既存の学生名とIDのマッピングを取得
    cursor.execute("SELECT id, name FROM students")
    existing_students = {row[1]: row[0] for row in cursor.fetchall()}

    # 既存のjournalsを削除（新しいデータで再構築）
    cursor.execute("DELETE FROM journals")
    cursor.execute("DELETE FROM insights")
    cursor.execute("DELETE FROM feedbacks")
    print("[CLEAR] 既存の journals/insights/feedbacks をクリア")

    total_journals = 0

    for name, dates in students_data.items():
        # 学生IDを取得（既存の学生のみ）
        student_id = existing_students.get(name)
        if student_id is None:
            print(f"  [WARN] 学生 {name} がstudentsテーブルに見つかりません。スキップ。")
            continue

        # 開始日を計算（最初の日誌日付）
        sorted_dates = sorted(dates.keys())
        if not sorted_dates:
            continue
        start_date = sorted_dates[0]

        # 各日のデータを投入
        for date_str in sorted_dates:
            entry = dates[date_str]

            # 空の日（欠席日等）はスキップ
            if not entry["practical_content"] and not entry["unachieved_point"]:
                continue

            week_num = calculate_week_number(date_str, start_date)

            # content_raw を構築
            content_parts = []
            if entry["practical_content"]:
                content_parts.append(f"【実習内容】\n{entry['practical_content']}")
            if entry["unachieved_point"]:
                content_parts.append(f"【達成できなかった点・反省】\n{entry['unachieved_point']}")
            content_raw = "\n\n".join(content_parts)

            cursor.execute(
                "INSERT INTO journals (student_id, date, week_number, content_raw) VALUES (?, ?, ?, ?)",
                (student_id, date_str, week_num, content_raw)
            )
            journal_id = cursor.lastrowid
            total_journals += 1

            # 薬剤師コメントを feedbacks に格納
            if entry["pharmacist_comment"]:
                cursor.execute(
                    "INSERT INTO feedbacks (journal_id, comment) VALUES (?, ?)",
                    (journal_id, entry["pharmacist_comment"])
                )

    conn.commit()

    # 結果報告
    cursor.execute("SELECT COUNT(*) FROM journals")
    journal_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM feedbacks")
    feedback_count = cursor.fetchone()[0]

    print(f"\n[OK] DB投入完了:")
    print(f"  - journals: {journal_count}件")
    print(f"  - feedbacks: {feedback_count}件")

    # 学生ごとの内訳
    cursor.execute("""
        SELECT s.name, COUNT(j.id) as cnt, 
               MIN(j.week_number) as min_week, MAX(j.week_number) as max_week
        FROM students s
        LEFT JOIN journals j ON s.id = j.student_id
        GROUP BY s.name
    """)
    print(f"\n  学生ごとの内訳:")
    for row in cursor.fetchall():
        print(f"    {row[0]}: {row[1]}件 (Week {row[2]}〜{row[3]})")

    conn.close()


def main():
    print("=" * 60)
    print("Kizuki-Log: 全PDF日誌データ投入パイプライン")
    print("=" * 60)

    # Step 1: PDFからテキスト抽出
    print("\n[Step 1] PDFからテキスト抽出")
    text_file = extract_text_from_pdfs()

    # Step 2: テキスト解析
    print("\n[Step 2] テキスト解析")
    students_data = parse_extracted_text(text_file)

    for name, dates in students_data.items():
        non_empty = sum(1 for d in dates.values() if d["practical_content"] or d["unachieved_point"])
        print(f"  {name}: {len(dates)}日分検出 (有効: {non_empty}日分)")

    # Step 3: DB投入
    print("\n[Step 3] DB投入")
    ingest_to_db(students_data)

    print("\n" + "=" * 60)
    print("パイプライン完了!")
    print("=" * 60)


if __name__ == "__main__":
    main()
