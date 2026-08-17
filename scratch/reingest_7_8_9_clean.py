"""
Re-ingest Standards 7, 8, 9 with corrected page-chapter maps.
Loads directly from cached OCR JSON files, cleans, chunks with accurate chapter maps, and indexes in ChromaDB.
Also removes Standard 10 chunks as instructed by the user.
"""
import sys
import json
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

from app.config.constants import AVAILABLE_STANDARDS
from app.embeddings.embedding_service import EmbeddingService
from app.vectorstore.chroma_service import ChromaService
from app.preprocessing.cleaner import TextCleaner
from app.preprocessing.chunker import TextChunker

STANDARDS_TO_REINGEST = [7, 8, 9]

print("Initializing EmbeddingService and ChromaService...")
emb = EmbeddingService()
emb.initialize()
chroma = ChromaService(embedding_service=emb)
chroma.create()

col = chroma._vectorstore._collection

# Step 0: Remove Standard 10 if present (user explicitly requested not to consider 10th std)
try:
    std10_res = col.get(where={"standard": 10})
    if std10_res and std10_res.get("ids"):
        print(f"\nRemoving {len(std10_res['ids'])} Std 10 chunks as requested...")
        col.delete(ids=std10_res["ids"])
        print("Std 10 chunks removed.")
except Exception as e:
    print(f"Note on removing Std 10: {e}")

cleaner = TextCleaner()
chunker = TextChunker()

for std in STANDARDS_TO_REINGEST:
    info = AVAILABLE_STANDARDS[std]
    cache_path = Path(f"data/{info['cache_filename']}")
    pdf_filename = info['pdf_filename']
    textbook_id = info['textbook_id']
    
    print(f"\n{'='*60}")
    print(f"Re-ingesting Standard {std} — {info['name']}")
    print('='*60)
    
    # 1. Delete existing chunks for this standard
    print(f"  Deleting existing Std {std} chunks from ChromaDB...")
    try:
        existing = col.get(where={"standard": std})
        if existing and existing.get("ids"):
            col.delete(ids=existing["ids"])
            print(f"  Deleted {len(existing['ids'])} existing chunks.")
        else:
            print("  No previous chunks found.")
    except Exception as e:
        print(f"  Warning during delete: {e}")
    
    # 2. Load cached OCR text
    if not cache_path.exists():
        print(f"  ERROR: Cache file {cache_path} not found!")
        continue
    
    with open(cache_path, "r", encoding="utf-8") as f:
        cache_data = json.load(f)
    
    print(f"  Loaded {len(cache_data)} pages from {cache_path}")
    
    # Format pages list
    pages = []
    for pg_str in sorted(cache_data.keys(), key=lambda x: int(x)):
        pg_num = int(pg_str)
        raw_text = cache_data[pg_str]
        if raw_text and raw_text.strip():
            cleaned_text = cleaner.clean(raw_text)
            if cleaned_text.strip():
                pages.append({"page_number": pg_num, "text": cleaned_text})
    
    print(f"  Cleaned {len(pages)} non-empty pages.")
    
    # 3. Chunk pages
    chunks = chunker.chunk_pages(
        pages=pages,
        source_filename=pdf_filename,
        standard=std,
        textbook_id=textbook_id,
    )
    print(f"  Generated {len(chunks)} chunks.")
    
    # Verify chapter breakdown
    from collections import Counter
    chapters = Counter(c.metadata.get("chapter", "unknown") for c in chunks)
    print(f"  Unique chapters in Std {std}: {len(chapters)}")
    for ch, count in chapters.most_common(6):
        print(f"    [{count:2d} chunks] {ch}")
    
    # 4. Add documents to ChromaDB
    print(f"  Embedding and adding {len(chunks)} chunks to ChromaDB...")
    chroma.add_documents(chunks)
    print(f"  ✅ Std {std} re-ingested successfully!")

# Final Verification
print(f"\n{'='*60}")
print("Final Database Verification Across Standards:")
print('='*60)
for s in [6, 7, 8, 9, 10]:
    try:
        res = col.get(where={"standard": s})
        count = len(res["ids"]) if res and "ids" in res else 0
        print(f"  Standard {s:2d}: {count:4d} chunks")
    except Exception as e:
        print(f"  Standard {s:2d}: ERROR {e}")

print(f"\nTotal documents in collection: {col.count()}")
