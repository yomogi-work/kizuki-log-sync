import sys
import json
sys.stdout.reconfigure(encoding='utf-8')
d = json.load(open('step0_data.json', 'r', encoding='utf-8'))
print(f"entries: {len(d['entries'])}")
print(f"buckets: {d['metadata']['buckets']}")
for e in d['entries'][:3]:
    print(f"  #{e['id']} {e['context']['student_name']} Week{e['context']['week_number']} {e['context']['journal_date']} text_len={len(e['entry_text'])}")
print(f"all have judgment=None: {all(e['judgment']['level'] is None for e in d['entries'])}")
