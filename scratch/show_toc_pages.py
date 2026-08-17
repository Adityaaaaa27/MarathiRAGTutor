import sys, json
sys.stdout.reconfigure(encoding='utf-8')

# Show TOC pages content for 7, 8, 9 to build chapter maps
caches = {
    7:  ('data/7th_ocr_cache.json',  [11, 12]),  # TOC was page 11
    8:  ('data/8th_ocr_cache.json',  [11, 12]),
    9:  ('data/9th_ocr_cache.json',  [10, 11, 12]),  # TOC page was 10 based on earlier scan
}

for std, (path, toc_pages) in caches.items():
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"\n{'='*70}")
    print(f"STD {std} — TOC pages content")
    print('='*70)
    for pg in toc_pages:
        pg_str = str(pg)
        if pg_str in data:
            print(f"\n--- Page {pg} ---")
            print(data[pg_str][:1500])
