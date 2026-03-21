import os
import urllib.request
import json

def list_details():
    api_key = os.environ.get('GEMINI_API_KEY', '')
    url = f'https://generativelanguage.googleapis.com/v1beta/models?key={api_key}'
    
    try:
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for model in data.get('models', []):
                name = model.get('name')
                methods = model.get('supportedGenerationMethods', [])
                print(f"Model: {name}, Methods: {methods}")
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
    list_details()
