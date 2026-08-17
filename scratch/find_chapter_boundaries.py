import sys, json
sys.stdout.reconfigure(encoding='utf-8')

# Scan for chapter boundaries
caches = {
    7: 'data/7th_ocr_cache.json',
    8: 'data/8th_ocr_cache.json',
    9: 'data/9th_ocr_cache.json',
}

import re

# Generic chapter heading pattern - matches at beginning of page
heading_pat = re.compile(
    r'^(?:(?:पाठ|धडा|कविता|संतवाणी|प्रार्थना|स्थूलवाचन)\s+)?'
    r'([१२३४५६७८९०]+|[0-9]+)\s*[.।:\-]\s*([^\n]{5,60})',
    re.MULTILINE | re.UNICODE
)

for std, path in caches.items():
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\nSTD {std} — {len(data)} pages total")
    
    # Print first 200 chars of each page 11-15 (cover, preamble skip)
    for pg_str in sorted(data.keys(), key=lambda x: int(x)):
        pg = int(pg_str)
        if pg < 11 or pg > 66:
            continue
        text = data[pg_str]
        if not text or not text.strip():
            continue
        head = text[:200].replace('\n', ' | ')
        print(f"  p{pg:3d}: {head[:120]}")
