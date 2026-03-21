import os
import urllib.request
import json

def test_gen(model_name):
    api_key = os.environ.get('GEMINI_API_KEY', '')
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}'
    
    payload = {
        "contents": [{"parts": [{"text": "Hello"}]}],
        "generationConfig": {"temperature": 0.7}
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            print(f"SUCCESS with {model_name}")
            return True
    except urllib.error.HTTPError as e:
        print(f"FAILED with {model_name}: {e.code} {e.reason}")
        print(e.read().decode('utf-8'))
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    env_path = '.env'
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, value = line.partition('=')
                    os.environ[key.strip()] = value.strip()
    
    test_gen("gemini-2.0-flash")
    test_gen("gemini-1.5-flash")
