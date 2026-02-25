import json
import re
import os

DATA_FILE = "dashboard_data.json"

def fix_data():
    if not os.path.exists(DATA_FILE):
        print(f"File not found: {DATA_FILE}")
        return

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    students = data.get("students", [])
    fixed_count = 0

    for student in students:
        for journal in student.get("journals", []):
            # 1. Fix Date Format (YYYY年MM月DD日 -> YYYY-MM-DD)
            if "年" in journal["date"]:
                match = re.match(r'(\d+)年(\d+)月(\d+)日', journal["date"])
                if match:
                    journal["date"] = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
                    fixed_count += 1
            
            # 2. Split Content if needed
            # content_raw is not standardized, but let's assume content has the mixed text
            # or we look at the 'content' field if practical_content is missing.
            # In imported data, we might have stored raw text in 'practical_content' initially?
            # Let's check logic: imported_students.json had separate fields?
            # imported_pdf_data.py logic:
            #   practical_content = ...
            #   unachieved_content = ...
            #   new_entry = { ..., "practical_content": ..., "unachieved_point": ... }
            # So imported data SHOULD be correct.
            # But the user report says "Specific Practical Content" was empty.
            # Ah, looking at import_pdf_data.py again...
            # It DOES populate practical_content and unachieved_point.
            # Maybe the browser verification failed because legacy 'content' field was used appropriately?
            # Or maybe I should ensure 'content' is synced with 'practical_content' for backward compat.

            # Ensure compatibility
            if "practical_content" not in journal:
                # Assuming old format where content was just practical
                journal["practical_content"] = journal.get("content", "")
            
            if "unachieved_point" not in journal:
                journal["unachieved_point"] = ""

            # If content has the split markers (from previous manual attempts?), clean it.
            # But let's trust that imported data logic was:
            # practical_content = extracted from "具体的な実習内容"
            # unachieved_point = extracted from "実習にて達成できなかった点"
            
            # Make sure 'content' field exists and mimics practical (or full?)
            if "content" not in journal:
                journal["content"] = journal["practical_content"]

    data["students"] = students

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Fixed {fixed_count} date entries and ensured structure.")

if __name__ == "__main__":
    fix_data()
