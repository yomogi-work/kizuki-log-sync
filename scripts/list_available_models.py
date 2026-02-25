import os
import urllib.request
import json

def list_flash_models():
    # .env から APIキーを取得
    api_key = ""
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    k, v = line.strip().split('=', 1)
                    if k.strip() == 'GEMINI_API_KEY':
                        api_key = v.strip()
    
    if not api_key:
        print("Error: GEMINI_API_KEY not found in .env")
        return

    # v1beta と v1 両方で利用可能なモデルを確認
    versions = ['v1beta', 'v1']
    for ver in versions:
        print(f"\n--- API Version: {ver} ---")
        url = f'https://generativelanguage.googleapis.com/{ver}/models?key={api_key}'
        try:
            with urllib.request.urlopen(url) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                for m in data.get('models', []):
                    name = m.get('name', '')
                    # 名前から 'models/' プレフィックスを抜いた ID を抽出
                    model_id = name.split('/')[-1]
                    methods = m.get('supportedGenerationMethods', [])
                    if 'generateContent' in methods:
                        print(f"ID: {model_id} (Full: {name})")
        except Exception as e:
            print(f"Error fetching {ver}: {e}")

if __name__ == "__main__":
    list_flash_models()
