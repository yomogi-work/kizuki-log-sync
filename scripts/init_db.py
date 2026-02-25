import sqlite3
import os

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Drop tables to ensure clean state
    cursor.execute('DROP TABLE IF EXISTS growth_triggers')
    cursor.execute('DROP TABLE IF EXISTS insights')
    cursor.execute('DROP TABLE IF EXISTS feedbacks')
    cursor.execute('DROP TABLE IF EXISTS journals')
    cursor.execute('DROP TABLE IF EXISTS students')

    # 1. Students
    cursor.execute('''
    CREATE TABLE students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        start_date TEXT
    )
    ''')

    # 2. Journals
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS journals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        date TEXT,
        week_number INTEGER,
        content_raw TEXT,
        FOREIGN KEY (student_id) REFERENCES students (id)
    )
    ''')

    # 3. Feedbacks
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS feedbacks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        journal_id INTEGER,
        comment TEXT,
        intent TEXT,
        FOREIGN KEY (journal_id) REFERENCES journals (id)
    )
    ''')

    # 4. Insights (Extracted "Kizuki")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS insights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        journal_id INTEGER,
        type TEXT,
        snippet TEXT,
        reason TEXT,
        FOREIGN KEY (journal_id) REFERENCES journals (id)
    )
    ''')

    # 5. Growth Triggers
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS growth_triggers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        date TEXT,
        description TEXT,
        FOREIGN KEY (student_id) REFERENCES students (id)
    )
    ''')

    conn.commit()
    conn.close()
    print(f"Database initialized at {db_path}")

if __name__ == "__main__":
    base_dir = "/Users/yomogiyakkyoku/Library/CloudStorage/OneDrive-株式会社ｗｏｒｍｗｏｏｄ/実習ツール類/Kizuki log"
    db_path = os.path.join(base_dir, "kizuki_log.db")
    init_db(db_path)
