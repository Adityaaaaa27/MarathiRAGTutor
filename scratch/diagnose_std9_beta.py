"""
Check what OCR text was extracted from Std 9 pages 17-21 (बेटा, मी एकटो आहे! chapter)
Compare with what's in ChromaDB chunks.
"""
import sys, json
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

# 1. Check the raw OCR cache for pages 17-21
ocr_cache_path = Path("data/ocr_cache/9th_ocr_cache.json")
print("=" * 70)
print("RAW OCR CACHE — Std 9 pages 17-21 (बेटा, मी एकटो आहे!)")
print("=" * 70)

if ocr_cache_path.exists():
    with open(ocr_cache_path, "r", encoding="utf-8") as f:
        cache = json.load(f)
    
    pages = cache.get("pages", [])
    for p in pages:
        pnum = p.get("page_number", p.get("page", -1))
        if 17 <= pnum <= 21:
            text = p.get("text", p.get("content", ""))
            print(f"\n--- Page {pnum} ---")
            print(f"Length: {len(text)} chars")
            print(f"Text:\n{text[:800]}")
            print(f"  ... [checking for घंटा] ...")
            if "घंटा" in text:
                # Find the context around it
                idx = text.find("घंटा")
                print(f"  FOUND 'घंटा' at pos {idx}: ...{text[max(0,idx-50):idx+100]}...")
            else:
                print("  ❌ 'घंटा' NOT FOUND in this page")
else:
    print(f"Cache file not found at {ocr_cache_path}")
    # Try alternate paths
    for p in Path("data").rglob("*9th*"):
        print(f"  Found: {p}")

# 2. Check what ChromaDB has for those pages
print("\n" + "=" * 70)
print("CHROMADB CHUNKS — Std 9 pages 17-21")
print("=" * 70)

from app.embeddings.embedding_service import EmbeddingService
from app.vectorstore.chroma_service import ChromaService

emb = EmbeddingService()
emb.initialize()
chroma = ChromaService(embedding_service=emb)
chroma.create()
col = chroma._vectorstore._collection

res = col.get(
    where={"$and": [{"standard": 9}, {"page_number": {"$gte": 17}}, {"page_number": {"$lte": 21}}]},
    include=["documents", "metadatas"]
)

docs = res["documents"]
metas = res["metadatas"]
print(f"Found {len(docs)} chunks for pages 17-21 in Std 9")

for doc, meta in zip(docs, metas):
    print(f"\n  Page {meta.get('page_number')} | Chapter: {meta.get('chapter')}")
    print(f"  Content: {doc[:400]}")
    if "घंटा" in doc:
        idx = doc.find("घंटा")
        print(f"  ✅ FOUND 'घंटा': ...{doc[max(0,idx-30):idx+80]}...")
    else:
        print("  ❌ 'घंटा' NOT in this chunk")
