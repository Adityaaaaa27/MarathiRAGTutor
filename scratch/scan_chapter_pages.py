import sys, json
sys.stdout.reconfigure(encoding='utf-8')

# Let's scan actual OCR content to understand page ranges per standard
caches = {
    7:  'data/7th_ocr_cache.json',
    8:  'data/8th_ocr_cache.json',
    9:  'data/9th_ocr_cache.json',
    10: 'data/10th_ocr_cache.json',
}

for std, path in caches.items():
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n{'='*70}")
    print(f"STD {std} — Page content scan (pages with chapter headings detected)")
    print('='*70)
    
    # Look for pages that have chapter/lesson headings
    import re
    patterns = [
        re.compile(r'(पाठ|धडा|कविता|संतवाणी|प्रार्थना|लेख|नाटक)\s*[।:\-–—]?\s*(.{5,60})', re.UNICODE),
        re.compile(r'(\d+|[१२३४५६७८९१०]+)\s*[.।]\s*(.{10,60})', re.UNICODE),
    ]
    
    chapter_pages = []
    for pg_str in sorted(data.keys(), key=lambda x: int(x)):
        text = data[pg_str]
        if not text or not text.strip():
            continue
        # Only check first 300 chars
        head = text[:300]
        for pat in patterns:
            m = pat.search(head)
            if m:
                chapter_pages.append((int(pg_str), m.group(0)[:80]))
                break
    
    # Show first 20 detected chapter headings
    for pg, heading in chapter_pages[:20]:
        print(f"  p{pg:3d}: {heading}")
    print(f"  ... total {len(chapter_pages)} pages with potential headings")
