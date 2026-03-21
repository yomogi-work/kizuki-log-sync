import sqlite3
import re
import os

def populate_db(db_path, text_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    with open(text_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by file boundary to get week context
    files = re.split(r'--- File: (.*?) ---', content)
    
    for i in range(1, len(files), 2):
        filename = files[i]
        file_content = files[i+1]
        
        # Determine week and year from filename
        match = re.search(r'_(.*?)_.*_(\d{4})(\d{2})(\d{2})', filename)
        if match:
            student_name = match.group(1).replace('\u3000', ' ').strip()
            year = match.group(2)
            date_part = f"{match.group(3)}{match.group(4)}"
            
            # Week detection based on date patterns provided
            if date_part in ['0519', '0217']: week = 1
            elif date_part in ['0616', '0317']: week = 5
            elif date_part in ['0728', '0428']: week = 11
            else: week = None
        else:
            continue
            
        # Ensure student exists (per file)
        cursor.execute('INSERT OR IGNORE INTO students (name) VALUES (?)', (student_name,))
        cursor.execute('SELECT id FROM students WHERE name = ?', (student_name,))
        student_id = cursor.fetchone()[0]
            
        # Dictionary to hold data for each day to merge content from multiple pages
        daily_data = {}
        
        # Split by day within file
        days = re.split(r'-- Page \d+ --\s*日誌\s*日誌 (\d{2}月\d{2}日)', file_content)
        
        for j in range(1, len(days), 2):
            date_key = f"{year}年{days[j]}"
            day_content = days[j+1]
            
            if date_key not in daily_data:
                daily_data[date_key] = {"student_text": "", "feedback": None}
            
            # Content part 1
            c1_match = re.search(r'具体的な実習内容(.*?)(?=実習に関する能力|-- Page|$)', day_content, re.DOTALL)
            if c1_match:
                content = c1_match.group(1).strip()
                if content and content not in daily_data[date_key]["student_text"]:
                    daily_data[date_key]["student_text"] += "【実習内容】\n" + content + "\n\n"
            
            # Content part 2
            c2_match = re.search(r'実習にて達成できなかった点\s*（次回への反省・改善点）(.*?)(?=添付資料|薬剤師のコメント|-- Page|$)', day_content, re.DOTALL)
            if c2_match:
                content = c2_match.group(1).strip()
                if content and content not in daily_data[date_key]["student_text"]:
                    daily_data[date_key]["student_text"] += "【反省点】\n" + content + "\n\n"
                
            # Extract Feedback
            fb_match = re.search(r'薬剤師のコメント(.*?)(?=登録者：|添付資料\(薬剤師\)|-- Page|$)', day_content, re.DOTALL)
            if fb_match:
                comment = fb_match.group(1).strip()
                if comment:
                    daily_data[date_key]["feedback"] = comment

        # Insert grouped data into DB
        for date_str, data in daily_data.items():
            if not data["student_text"].strip():
                continue
                
            cursor.execute('''
                INSERT INTO journals (student_id, date, week_number, content_raw)
                VALUES (?, ?, ?, ?)
            ''', (student_id, date_str, week, data["student_text"].strip()))
            journal_id = cursor.lastrowid
            
            if data["feedback"]:
                cursor.execute('''
                    INSERT INTO feedbacks (journal_id, comment)
                    VALUES (?, ?)
                ''', (journal_id, data["feedback"]))

    conn.commit()
    conn.close()
    print("Database population complete.")

if __name__ == "__main__":
    base_dir = "/Users/yomogiyakkyoku/Library/CloudStorage/OneDrive-株式会社ｗｏｒｍｗｏｏｄ/実習ツール類/Kizuki log"
    db_path = os.path.join(base_dir, "kizuki_log.db")
    text_path = os.path.join(base_dir, "raw_data/extracted_text.txt")
    populate_db(db_path, text_path)
