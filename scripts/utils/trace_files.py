import os
import json

search_root = r'C:\Users\NOAH\OneDrive - 株式会社 ｗｏｒｍｗｏｏｄ'
results = []

for root, dirs, files in os.walk(search_root):
    if 'dashboard_data.json' in files or 'start_server.py' in files:
        for f in files:
            if f in ['dashboard_data.json', 'start_server.py']:
                path = os.path.join(root, f)
                info = {"path": path}
                if f == 'dashboard_data.json':
                    try:
                        with open(path, 'r', encoding='utf-8') as jf:
                            data = json.load(jf)
                            info["names"] = [s['name'] for s in data.get('students', [])]
                    except Exception as e:
                        info["error"] = str(e)
                results.append(info)

print(json.dumps(results, indent=2, ensure_ascii=False))
