import json
import os

def inspect_yagi():
    try:
        with open('dashboard_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        students = data.get('students', [])
        yagi = next((s for s in students if '八木' in s.get('name', '')), None)
        
        if not yagi:
            print("Student '八木' not found.")
            return

        print(f"Found student: {yagi['name']} (ID: {yagi['id']})")
        print(f"Total journals: {len(yagi.get('journals', []))}")
        
        journals = sorted(yagi.get('journals', []), key=lambda x: x.get('date', ''))
        for j in journals:
            print(f"Date: {j.get('date')}")
            print(f"  Practical Content (Daily Guidance): {j.get('practical_content', '')[:50]}...")
            print(f"  Unachieved Point (Prep): {j.get('unachieved_point', '')[:50]}...")
            print("-" * 20)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_yagi()
