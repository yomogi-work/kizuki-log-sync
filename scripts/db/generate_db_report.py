import sqlite3

def generate_report():
    conn = sqlite3.connect('kizuki_log.db')
    cursor = conn.cursor()
    
    with open('db_schema_report.txt', 'w', encoding='utf-8') as f:
        # Get all tables
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = cursor.fetchall()
        
        f.write("=== Kizuki-Log Database Schema Report ===\n\n")
        
        for table_name, create_sql in tables:
            f.write(f"--- Table: {table_name} ---\n")
            f.write(f"Definition:\n{create_sql}\n\n")
            
            f.write("Columns:\n")
            cursor.execute(f"PRAGMA table_info({table_name});")
            for col in cursor.fetchall():
                pk_str = " (PRIMARY KEY)" if col[5] else ""
                nn_str = " NOT NULL" if col[3] else ""
                f.write(f"  - {col[1]} ({col[2]}){nn_str}{pk_str}\n")
            
            f.write("\nIndexes:\n")
            cursor.execute(f"PRAGMA index_list({table_name});")
            for idx in cursor.fetchall():
                idx_name = idx[1]
                f.write(f"  - {idx_name} (Unique: {idx[2]})\n")
                cursor.execute(f"PRAGMA index_info({idx_name});")
                for c in cursor.fetchall():
                    f.write(f"    - Column: {c[2]}\n")
            f.write("\n" + "="*40 + "\n\n")

        f.write("--- Triggers ---\n")
        cursor.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='trigger';")
        for name, tbl, sql in cursor.fetchall():
            f.write(f"Trigger: {name} (on {tbl})\n{sql}\n\n")

    conn.close()

if __name__ == "__main__":
    generate_report()
