import json
import os

def final_fix():
    file_path = 'dashboard_data.json'
    bak_path = 'dashboard_data.json.repair_bak'
    
    if not os.path.exists(bak_path):
        print(f"Error: {bak_path} does not exist.")
        return

    try:
        with open(bak_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        initial_count = len(data['students'])
        data['students'] = [s for s in data['students'] if s.get('id') != 1770857352358 and s.get('name') != '八木 仁']
        final_count = len(data['students'])
        
        print(f"Removing {initial_count - final_count} students.")
        
        # Write to a temporary file first
        temp_path = 'dashboard_data_temp.json'
        with open(temp_path, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        # Verify the temp file is valid JSON
        with open(temp_path, 'r', encoding='utf-8') as f:
            json.load(f)
            
        # Atomic replace
        if os.path.exists(file_path):
            os.remove(file_path)
        os.rename(temp_path, file_path)
        print("Successfully written clean JSON to dashboard_data.json")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    final_fix()
