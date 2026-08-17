import sys, json, os
sys.stdout.reconfigure(encoding='utf-8')

files = {
    '6':  'data/6th_ocr_cache.json',
    '7':  'data/7th_ocr_cache.json',
    '8':  'data/8th_ocr_cache.json',
    '9':  'data/9th_ocr_cache.json',
    '10': 'data/10th_ocr_cache.json',
}

for std, path in files.items():
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        pages = list(data.keys())
        empty = [p for p, v in data.items() if not v or not v.strip()]
        non_empty = len(pages) - len(empty)
        print(f'Std {std}: {len(pages)} pages cached | {non_empty} non-empty | {len(empty)} empty')
        sample_key = next((p for p, v in data.items() if v and v.strip()), None)
        if sample_key:
            snippet = data[sample_key][:120].replace('\n', ' ')
            print(f'  Sample p{sample_key}: {snippet}')
    else:
        print(f'Std {std}: CACHE FILE MISSING at {path}')
