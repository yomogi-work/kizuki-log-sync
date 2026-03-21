import os
import urllib.request
import json

def fetch_all_models():
    env = {}
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, _, v = line.partition('=')
                    env[k.strip()] = v.strip()
    
    api_key = env.get('GEMINI_API_KEY')
    if not api_key:
        print("API Key not found")
        return

    # v1beta でリスト取得
    url = f'https://generativelanguage.googleapis.com/v1beta/models?key={api_key}'
    try:
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            with open('all_models_full.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print("Successfully saved all_models_full.json")
            
            print("\nAvailable Gemini Models:")
            for m in data.get('models', []):
                name = m.get('name', '')
                if 'gemini' in name:
                    methods = m.get('supportedGenerationMethods', [])
                    print(f"- {name} (Gen: {'GenerateContent' in methods})")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_all_models()
