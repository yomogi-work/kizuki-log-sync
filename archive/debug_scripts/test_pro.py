import os
import urllib.request
import json

def test_pro():
    env = {}
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, _, v = line.partition('=')
                    env[k.strip()] = v.strip()
    
    api_key = env.get('GEMINI_API_KEY')
    model = "gemini-1.5-pro"
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}'
    
    payload = {"contents": [{"parts": [{"text": "Hello"}]}]}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"SUCCESS with {model}")
    except urllib.error.HTTPError as e:
        print(f"FAILED with {model}: {e.code} {e.reason}")
        print(e.read().decode('utf-8'))

if __name__ == "__main__":
    test_pro()
