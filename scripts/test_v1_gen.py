import os
import urllib.request
import json

def test_v1_generate():
    path = '.env'
    env = {}
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, value = line.partition('=')
                    env[key.strip()] = value.strip()
    
    api_key = env.get('GEMINI_API_KEY')
    model = "gemini-1.5-flash"
    # v1 を使用
    url = f'https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={api_key}'
    
    payload = {
        "contents": [{"parts": [{"text": "Hello"}]}],
        "generationConfig": {"temperature": 0.7}
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            print(f"v1 SUCCESS with {model}")
            return True
    except urllib.error.HTTPError as e:
        print(f"v1 FAILED with {model}: {e.code} {e.reason}")
        print(e.read().decode('utf-8'))
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    test_v1_generate()
