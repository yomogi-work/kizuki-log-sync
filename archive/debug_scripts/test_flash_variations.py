import os
import urllib.request
import urllib.error
import json

def test_variation(version, model):
    env = {}
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    k, v = line.strip().split('=', 1)
                    env[k.strip()] = v.strip()
    
    api_key = env.get('GEMINI_API_KEY')
    url = f'https://generativelanguage.googleapis.com/{version}/models/{model}:generateContent?key={api_key}'
    
    payload = {"contents": [{"parts": [{"text": "Hi"}]}]}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"[{version}] {model}: SUCCESS")
            return True
    except urllib.error.HTTPError as e:
        print(f"[{version}] {model}: {e.code}")
        return False
    except Exception as e:
        print(f"[{version}] {model}: ERROR {str(e)}")
        return False

if __name__ == "__main__":
    candidates = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-1.5-flash-001", "gemini-1.5-flash-002", "gemini-1.5-flash-8b"]
    for v in ["v1beta", "v1"]:
        for c in candidates:
            test_variation(v, c)
