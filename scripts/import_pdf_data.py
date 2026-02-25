import re
import json
import datetime

# Source file path
SOURCE_FILE = "/Users/yomogiyakkyoku/Library/CloudStorage/OneDrive-株式会社ｗｏｒｍｗｏｏｄ/実習ツール類/Kizuki log/raw_data/extracted_text.txt"
OUTPUT_FILE = "/Users/yomogiyakkyoku/Library/CloudStorage/OneDrive-株式会社ｗｏｒｍｗｏｏｄ/実習ツール類/Kizuki log/raw_data/imported_students.json"

def parse_date(date_str, filename_year):
    # date_str format: "MM月DD日"
    try:
        match = re.search(r'(\d+)月(\d+)日', date_str)
        if match:
            month = int(match.group(1))
            day = int(match.group(2))
            
            # Use year from filename or assume 2025/2026 based on logic if needed.
            # Filenames have format YYYYMMDD in the text structure "--- File: ..._YYYYMMDD.pdf ---"
            # We can pass the year extracted from the file header.
            year = int(filename_year) if filename_year else 2025
            
            return f"{year}-{month:02d}-{day:02d}"
    except Exception as e:
        print(f"Error parsing date: {date_str} - {e}")
    return None

def extract_data():
    with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by file headers to handle multiple files
    files = re.split(r'--- File: (.*?) ---', content)[1:] # Skip empty first split
    
    students_data = {}

    for i in range(0, len(files), 2):
        filename = files[i]
        file_content = files[i+1]
        
        # Extract Year from filename (e.g., ..._20250519.pdf)
        year_match = re.search(r'_(\d{4})\d{4}\.pdf', filename)
        year = year_match.group(1) if year_match else "2025"

        # Split by pages
        pages = re.split(r'-- Page \d+ --', file_content)

        for page in pages:
            if not page.strip():
                continue

            # Extract Name
            name_match = re.search(r'氏名\(\s*(.*?)\s*\)', page)
            if not name_match:
                continue
            name = name_match.group(1).replace("　", " ").strip() # Normalize space

            # Extract Date
            date_match = re.search(r'日誌 (\d+月\d+日)', page)
            if not date_match:
                continue
            date_str = date_match.group(1)
            formatted_date = parse_date(date_str, year)
            
            if not formatted_date:
                continue

            # Initialize student if not exists
            if name not in students_data:
                students_data[name] = {
                    "id": abs(hash(name)) % 100000000 + 1000, # Simple deterministic ID
                    "name": name,
                    "journals": [],
                    "growth_triggers": [],
                    "insights": [],
                    "settings": {} # Will calculate later
                }

            # Extract "具体的な実習内容"
            # Allows multiline capture until next "実習に関する能力" or similar section header
            # Note: The text might be fragmented. We look for the start and a likely end.
            practical_content = ""
            practical_match = re.search(r'具体的な実習内容(.*?)(?=実習に関する能力|-- Page|$)', page, re.DOTALL)
            if practical_match:
                practical_content = practical_match.group(1).strip()

            # Extract "実習にて達成できなかった点"
            unachieved_content = ""
            unachieved_match = re.search(r'実習にて達成できなかった点\s*\n\s*（次回への反省・改善点）(.*?)(?=添付資料|薬剤師のコメント|-- Page|$)', page, re.DOTALL)
            if unachieved_match:
                unachieved_content = unachieved_match.group(1).strip()
            
            # Combine or check if existing (some pages might be continuations, but here each page seems to have a date header)
            # The structure suggests one journal entry per day, but split across pages?
            # Looking at the file, Page 2 has "具体的な実習内容", Page 4 has "実習にて達成できなかった点".
            # They share the same date "05月19日".
            
            # Check if we already have an entry for this date
            existing_entry = next((j for j in students_data[name]["journals"] if j["date"] == formatted_date), None)
            
            if existing_entry:
                if practical_content and not existing_entry.get("practical_content"):
                    existing_entry["content"] = practical_content # Backward compatibility
                    existing_entry["practical_content"] = practical_content
                if unachieved_content and not existing_entry.get("unachieved_point"):
                    existing_entry["unachieved_point"] = unachieved_content
            else:
                if practical_content or unachieved_content:
                    # Create new entry
                    # Calculate week number (Rough estimate or logic?)
                    # For now default to 1, will refine.
                    new_entry = {
                        "id": int(formatted_date.replace("-", "")),
                        "date": formatted_date,
                        "content": practical_content, # Should be deprecated or keep valid for display
                        "practical_content": practical_content,
                        "unachieved_point": unachieved_content,
                        "week_number": 1 # Placeholder
                    }
                    students_data[name]["journals"].append(new_entry)

    # Post-process to calculate stats and clean up
    final_students = []
    
    for name, data in students_data.items():
        # Sort journals by date
        data["journals"].sort(key=lambda x: x["date"])
        
        if not data["journals"]:
            continue
            
        # Determine Start and End Date (Mon of first week to Sun of 11th week)
        # First, find the very first date in journals as a reference point for "Start Date"
        # However, user said "Week 1 Day 1" is the start.
        # Let's assume the first journal entry date is close to start date.
        # Actually, let's just take the min recorded date as start_date for now.
        
        dates = [j["date"] for j in data["journals"]]
        min_date = min(dates)
        
        # Calculate start date (Assume it matches the first journal, usually Monday)
        start_date_obj = datetime.datetime.strptime(min_date, "%Y-%m-%d")
        
        # Calculate End Date: +11 weeks (approx 77 days) - adjusted to Sunday
        # Logic: 11th week's Sunday.
        # Week 1 starts on start_date_obj.
        # Week 11 end = start_date_obj + 10 weeks + (days until sunday)
        # Actually, "Week 11 Last Day Sunday" implies specific duration.
        # Let's set end date to start_date + 11 weeks for approximate.
        end_date_obj = start_date_obj + datetime.timedelta(weeks=11)
        # Adjust to Sunday? Let's keep it simple for now or use the logic if strict.
        
        data["settings"] = {
            "startDate": min_date,
            "endDate": end_date_obj.strftime("%Y-%m-%d"),
            "goal": "実習を通じて成長する", # Default
            "interests": "未設定"
        }
        
        # Assign Week Numbers based on start date
        for journal in data["journals"]:
             j_date = datetime.datetime.strptime(journal["date"], "%Y-%m-%d")
             days_diff = (j_date - start_date_obj).days
             week_num = (days_diff // 7) + 1
             journal["week_number"] = week_num

        final_students.append(data)

    # Output to JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump({"students": final_students}, f, ensure_ascii=False, indent=2)

    print(f"Imported {len(final_students)} students. Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    extract_data()
