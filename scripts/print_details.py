import os

def print_details():
    path = r'c:\Users\NOAH\OneDrive - 株式会社 ｗｏｒｍｗｏｏｄ\実習ツール類\Kizuki log\scripts\details.txt'
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            for line in lines:
                print(line.strip())
    else:
        print(f"File not found: {path}")

if __name__ == "__main__":
    print_details()
