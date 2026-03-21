import urllib.request
import json

try:
    url = 'http://localhost:8080/dashboard_data.json'
    with urllib.request.urlopen(url) as response:
        content = response.read().decode('utf-8')
        data = json.loads(content)
        print("URL:", url)
        print("NAMES:", [s['name'] for s in data.get('students', [])])
except Exception as e:
    print("ERROR:", e)
