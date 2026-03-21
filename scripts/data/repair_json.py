import json
import os

file_path = 'dashboard_data.json'
bak_path = 'dashboard_data.json.repair_bak'

# Read the file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Try to find the valid JSON part
# We know it starts with { and should end with }
# There might be multiple closing braces, we want the one that balances the first {

valid_json = ""
try:
    # A simple way to fix the extra data is to find the LAST closing brace that makes it valid
    for i in range(len(content), 0, -1):
        try:
            candidate = content[:i]
            data = json.loads(candidate)
            valid_json = candidate
            print(f"Found valid JSON at length {i}")
            break
        except json.JSONDecodeError:
            continue
except Exception as e:
    print(f"Error finding valid JSON: {e}")

if valid_json:
    # Backup
    os.rename(file_path, bak_path)
    
    # Process the valid data
    data = json.loads(valid_json)
    
    # Remove "八木 仁"
    initial_count = len(data['students'])
    data['students'] = [s for s in data['students'] if s.get('id') != 1770857352358 and s.get('name') != '八木 仁']
    final_count = len(data['students'])
    
    print(f"Removed {initial_count - final_count} student(s).")
    
    # Save clean JSON
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Cleaned JSON saved successfully.")
else:
    print("Could not find any valid JSON prefix.")
