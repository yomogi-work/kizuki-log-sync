import json

try:
    with open('dashboard_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Total students: {len(data.get('students', []))}")
    for s in data.get('students', []):
        print(f"- {s.get('name')} (ID: {s.get('id')})")

except Exception as e:
    print(f"Error: {e}")
