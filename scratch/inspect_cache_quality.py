import sys, json
sys.stdout.reconfigure(encoding='utf-8')

caches = {
    7:  'data/7th_ocr_cache.json',
    8:  'data/8th_ocr_cache.json',
    9:  'data/9th_ocr_cache.json',
    10: 'data/10th_ocr_cache.json',
}

for std, path in caches.items():
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Find a content page (not cover page) - try pages 10-20
    print(f"\n{'='*60}")
    print(f"STD {std} — Pages 10-14 content sample:")
    print('='*60)
    for pg in ['10', '11', '12', '13', '14']:
        if pg in data and data[pg] and data[pg].strip():
            print(f"\n--- Page {pg} ---")
            print(data[pg][:400])
            break
    
    # Check garbled entries (markers like [B, [BLANK, [No Marathi)
    garbled = {p: v for p, v in data.items() if v and (
        '[B' in v or '[BLANK' in v.upper() or 'No Marathi' in v or 
        'no Marathi' in v or 'not available' in v.lower() or
        'image' in v.lower()[:30]
    )}
    print(f"\nPotentially garbled/blank pages: {len(garbled)} of {len(data)}")
    if garbled:
        sample_pg = next(iter(garbled))
        print(f"  Example (page {sample_pg}): {repr(garbled[sample_pg][:150])}")
