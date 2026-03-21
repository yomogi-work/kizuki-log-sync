import sqlite3

def find_yagi():
    conn = sqlite3.connect('kizuki_log.db')
    cursor = conn.cursor()
    
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall() if not t[0].startswith('sqlite_')]
    print(f"Tables: {tables}")
    
    for table in tables:
        print(f"\n--- Scanning {table} ---")
        cursor.execute(f"PRAGMA table_info({table});")
        cols = [c[1] for c in cursor.fetchall()]
        
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        for row in rows:
            if any("八木" in str(cell) for cell in row):
                print(f"MATCH in {table}: {dict(zip(cols, row))}")
    
    conn.close()

if __name__ == "__main__":
    find_yagi()
