import os
import urllib.request
import json

def list_models():
    api_key = os.environ.get('GEMINI_API_KEY', '')
    if not api_key:
        print("GEMINI_API_KEY not found in environment.")
        return

    url = f'https://generativelanguage.googleapis.com/v1beta/models?key={api_key}'
    
    try:
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for model in data.get('models', []):
                print(model.get('name'))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # .env を読み込む
    env_path = '.env'
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, value = line.partition('=')
                    os.environ[key.strip()] = value.strip()
    
    list_models()
