"""
Search entire Std 9 OCR cache for 'घंटा' and check page 17-21 text length 
to detect missing/thin OCR pages.
"""
import sys, json
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

# Find the OCR cache
possible_paths = [
    "data/ocr_cache/9th_ocr_cache.json",
    "data/9th_ocr_cache.json",
    "ocr_cache/9th_ocr_cache.json",
    "cache/9th_ocr_cache.json",
]

cache = None
for p in possible_paths:
    path = Path(p)
    if path.exists():
        print(f"Found cache at: {p}")
        with open(path, "r", encoding="utf-8") as f:
            cache = json.load(f)
        break

if not cache:
    # Search recursively
    for f in Path(".").rglob("9th*cache*.json"):
        print(f"Found: {f}")
    sys.exit(1)

pages = cache.get("pages", [])
print(f"Total pages in cache: {len(pages)}")

print("\n=== Searching for 'घंटा' across ALL pages ===")
for p in pages:
    pnum = p.get("page_number", p.get("page", -1))
    text = p.get("text", p.get("content", ""))
    if "घंटा" in text:
        idx = text.find("घंटा")
        print(f"  Page {pnum}: FOUND at pos {idx} -> ...{text[max(0,idx-80):idx+120]}...")

print("\n=== Page lengths for pages 17-21 (check for thin/missing OCR) ===")
for p in pages:
    pnum = p.get("page_number", p.get("page", -1))
    if 17 <= pnum <= 21:
        text = p.get("text", p.get("content", ""))
        print(f"  Page {pnum}: {len(text)} chars")
        print(f"    First 300: {text[:300].replace(chr(10), ' ')}")
        print()

print("\n=== Full text of page 18 (where story should be) ===")
for p in pages:
    pnum = p.get("page_number", p.get("page", -1))
    if pnum == 18:
        text = p.get("text", p.get("content", ""))
        print(f"FULL PAGE 18 TEXT ({len(text)} chars):")
        print(text)
