import json

def list_students():
    try:
        with open('dashboard_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            for s in data['students']:
                print(f"ID: {s.get('id')}, Name: {s.get('name')}")
    except Exception as e:
        print(f"Error: {e}")
        # Try to debug the end of the file
        with open('dashboard_data.json', 'r', encoding='utf-8') as f:
            content = f.read()
            print("\nLast 200 characters of file:")
            print(repr(content[-200:]))

if __name__ == "__main__":
    list_students()
