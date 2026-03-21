import os
import urllib.request
import urllib.error
import json

def diagnose():
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    k, v = line.strip().split('=', 1)
                    os.environ[k.strip()] = v.strip()
    
    api_key = os.environ.get('GEMINI_API_KEY')
    model = os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash')
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}'
    
    print(f"Testing URL: {url.replace(api_key, 'HIDDEN')}")
    
    payload = {"contents": [{"parts": [{"text": "Hello"}]}]}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    
    try:
        with urllib.request.urlopen(req) as resp:
            print("SUCCESS: Connection established.")
    except urllib.error.HTTPError as e:
        print(f"RESULT_CODE: {e.code}")
        print(f"RESULT_BODY: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"RESULT_ERROR: {str(e)}")

if __name__ == "__main__":
    diagnose()
