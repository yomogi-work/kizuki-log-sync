import os
from pypdf import PdfReader

def extract_text_from_pdfs(directory):
    pdf_files = [f for f in os.listdir(directory) if f.endswith('.pdf')]
    pdf_files.sort()
    
    for filename in pdf_files:
        path = os.path.join(directory, filename)
        print(f"--- File: {filename} ---")
        try:
            reader = PdfReader(path)
            for i, page in enumerate(reader.pages):
                print(f"-- Page {i+1} --")
                print(page.extract_text())
        except Exception as e:
            print(f"Error reading {filename}: {e}")
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    data_dir = "/Users/yomogiyakkyoku/Library/CloudStorage/OneDrive-株式会社ｗｏｒｍｗｏｏｄ/実習ツール類/Kizuki log/raw_data"
    extract_text_from_pdfs(data_dir)
