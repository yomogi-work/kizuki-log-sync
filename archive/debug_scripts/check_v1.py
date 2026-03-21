import os
import urllib.request
import json

def check_v1():
    api_key = os.environ.get('GEMINI_API_KEY', '')
    # v1 エンドポイントを使用
    url = f'https://generativelanguage.googleapis.com/v1/models?key={api_key}'
    
    try:
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            models = [m.get('name') for m in data.get('models', [])]
            for m in models:
                if 'flash' in m.lower():
                    print(f"v1 model: {m}")
    except Exception as e:
        print(f"v1 Error: {e}")

if __name__ == "__main__":
    env_path = '.env'
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, value = line.partition('=')
                    os.environ[key.strip()] = value.strip()
    check_v1()
