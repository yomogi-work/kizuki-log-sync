import os
import urllib.request
import json

def get_env():
    env = {}
    path = '.env'
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, value = line.partition('=')
                    env[key.strip()] = value.strip()
    return env

def list_gemini_models():
    env = get_env()
    api_key = env.get('GEMINI_API_KEY')
    if not api_key:
        print("API Key not found in .env")
        return

    url = f'https://generativelanguage.googleapis.com/v1beta/models?key={api_key}'
    try:
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            gemini_models = [m['name'] for m in data.get('models', []) if 'gemini' in m['name']]
            print("--- Gemini Models Found ---")
            for m in gemini_models:
                print(m)
            print("---------------------------")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_gemini_models()
