import sqlite3
import json

def get_detailed_schema():
    conn = sqlite3.connect('kizuki_log.db')
    cursor = conn.cursor()
    
    schema_info = {}
    
    # Get all tables
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = cursor.fetchall()
    
    for table_name, create_sql in tables:
        schema_info[table_name] = {
            "columns": [],
            "indexes": [],
            "create_sql": create_sql
        }
        
        # Get columns info
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        for col in columns:
            schema_info[table_name]["columns"].append({
                "cid": col[0],
                "name": col[1],
                "type": col[2],
                "notnull": col[3],
                "pk": col[5]
            })
            
        # Get indexes info
        cursor.execute(f"PRAGMA index_list({table_name});")
        indexes = cursor.fetchall()
        for idx in indexes:
            idx_name = idx[1]
            cursor.execute(f"PRAGMA index_info({idx_name});")
            idx_cols = cursor.fetchall()
            schema_info[table_name]["indexes"].append({
                "name": idx_name,
                "unique": idx[2],
                "columns": [c[2] for c in idx_cols]
            })

    # Get triggers info
    cursor.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='trigger';")
    triggers = cursor.fetchall()
    trigger_info = []
    for name, tbl, sql in triggers:
        trigger_info.append({"name": name, "table": tbl, "sql": sql})
    
    conn.close()
    
    full_report = {
        "tables": schema_info,
        "triggers": trigger_info
    }
    print(json.dumps(full_report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    get_detailed_schema()
