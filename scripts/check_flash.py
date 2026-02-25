import os
import urllib.request
import json

def check_flash_models():
    api_key = os.environ.get('GEMINI_API_KEY', '')
    url = f'https://generativelanguage.googleapis.com/v1beta/models?key={api_key}'
    
    try:
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            models = [m.get('name') for m in data.get('models', [])]
            print("Found models:")
            for m in models:
                if 'flash' in m.lower():
                    print(f"  - {m}")
            
            target = "models/gemini-1.5-flash"
            if target in models:
                print(f"SUCCESS: {target} is available.")
            else:
                print(f"FAILURE: {target} is NOT available.")
                # 近い名前を探す
                import difflib
                matches = difflib.get_close_matches(target, models)
                print(f"Did you mean? {matches}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    env_path = '.env'
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, value = line.partition('=')
                    os.environ[key.strip()] = value.strip()
    check_flash_models()
