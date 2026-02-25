import json
import os
import datetime

files = [
    'dashboard_data.json',
    'dashboard_data.json.bak',
    'dashboard_data.json.repair_bak'
]

def inspect_file(filename):
    print(f"--- Checking {filename} ---")
    if not os.path.exists(filename):
        print("File not found.")
        return

    mtime = os.path.getmtime(filename)
    dt = datetime.datetime.fromtimestamp(mtime)
    print(f"Last Modified: {dt}")

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        yagi = next((s for s in data.get('students', []) if '八木' in s.get('name', '')), None)
        
        if yagi:
            journals = yagi.get('journals', [])
            print(f"Student: {yagi['name']}")
            print(f"Journal Count: {len(journals)}")
            if len(journals) > 0:
                print(f"Latest Journal Date: {journals[-1].get('date', 'N/A')}")
        else:
            print("Student '八木' not found.")
            
    except Exception as e:
        print(f"Error reading file: {e}")
    print("\n")

if __name__ == "__main__":
    with open('backup_report_utf8.txt', 'w', encoding='utf-8') as report_file:
        import sys
        original_stdout = sys.stdout
        sys.stdout = report_file
        for f in files:
            inspect_file(f)
        sys.stdout = original_stdout
