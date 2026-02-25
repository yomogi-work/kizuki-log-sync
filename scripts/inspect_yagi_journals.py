import json

try:
    with open('dashboard_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    yagi = next((s for s in data.get('students', []) if '八木' in s.get('name', '')), None)
    
    if yagi:
        print(f"Student: {yagi['name']}")
        journals = yagi.get('journals', [])
        print(f"Journal Count: {len(journals)}")
        for j in journals:
            print(f"Date: {j.get('date')}")
            print(f"  Practical: {len(j.get('practical_content', '') or '')} chars")
            print(f"  Unachieved: {len(j.get('unachieved_point', '') or '')} chars")
            print(f"  Instructor Notes: {len(j.get('instructor_notes', '') or '')} chars")
            print("-" * 20)
    else:
        print("Yagi not found")

except Exception as e:
    print(f"Error: {e}")
