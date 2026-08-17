import sys, json, re
sys.stdout.reconfigure(encoding='utf-8')

caches = {
    7:  'data/7th_ocr_cache.json',
    8:  'data/8th_ocr_cache.json',
    9:  'data/9th_ocr_cache.json',
}

for std, path in caches.items():
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n{'='*70}")
    print(f"STD {std} — Page content scan")
    print('='*70)
    
    for pg_str in sorted(data.keys(), key=lambda x: int(x)):
        text = data[pg_str]
        if not text or not text.strip():
            continue
        # Show first 200 chars of each page so we can build the chapter map
        head = text[:200].replace('\n', ' | ')
        print(f"  p{int(pg_str):3d}: {head}")
