import json
import os
import shutil

# Paths
DASHBOARD_DATA_FILE = "dashboard_data.json"
IMPORTED_DATA_FILE = "raw_data/imported_students.json"
BACKUP_FILE = "dashboard_data.json.bak"

def merge_data():
    # 1. Load existing dashboard data
    if os.path.exists(DASHBOARD_DATA_FILE):
        with open(DASHBOARD_DATA_FILE, 'r', encoding='utf-8') as f:
            dashboard_data = json.load(f)
        
        # Backup existing data
        shutil.copy2(DASHBOARD_DATA_FILE, BACKUP_FILE)
        print(f"Backed up existing data to {BACKUP_FILE}")
    else:
        print(f"Warning: {DASHBOARD_DATA_FILE} not found. Creating new.")
        dashboard_data = {"students": []}

    # 2. Load imported data
    if os.path.exists(IMPORTED_DATA_FILE):
        with open(IMPORTED_DATA_FILE, 'r', encoding='utf-8') as f:
            imported_data = json.load(f)
    else:
        print(f"Error: {IMPORTED_DATA_FILE} not found.")
        return

    # 3. Merge strategies
    existing_students = dashboard_data.get("students", [])
    imported_students = imported_data.get("students", [])

    # Create a map of existing student IDs and Names for quick lookup
    existing_ids = {s["id"] for s in existing_students}
    existing_names = {s["name"] for s in existing_students}

    added_count = 0
    skipped_count = 0

    for student in imported_students:
        # Check by ID or Name to avoid duplicates (Name is safer here as IDs might be random)
        if student["name"] in existing_names:
            print(f"Skipping {student['name']} (Already exists)")
            skipped_count += 1
            continue
        
        # Ensure unique ID if collision (though unlikely with current hash)
        if student["id"] in existing_ids:
            print(f"ID collision for {student['name']}, regenerating ID...")
            student["id"] = student["id"] + 9999 # Simple offset
        
        existing_students.append(student)
        existing_ids.add(student["id"])
        existing_names.add(student["name"])
        added_count += 1
        print(f"Added {student['name']}")

    dashboard_data["students"] = existing_students

    # 4. Save merged data
    with open(DASHBOARD_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(dashboard_data, f, ensure_ascii=False, indent=2)

    print(f"Merge complete. Added: {added_count}, Skipped: {skipped_count}")

if __name__ == "__main__":
    merge_data()
