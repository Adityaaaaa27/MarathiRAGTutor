"""
Re-ingest Standards 7, 8, 9 with corrected page-chapter maps.
This clears and re-adds only those standards' chunks in ChromaDB.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

from app.config.constants import AVAILABLE_STANDARDS
from app.embeddings.embedding_service import EmbeddingService
from app.vectorstore.chroma_service import ChromaService
from app.ingestion.pdf_loader_ocr import PDFLoader
from app.preprocessing.cleaner import TextCleaner
from app.preprocessing.chunker import TextChunker

STANDARDS_TO_REINGEST = [7, 8, 9]

print("Initializing services...")
emb = EmbeddingService()
emb.initialize()
chroma = ChromaService(embedding_service=emb)
chroma.create()

col = chroma._vectorstore._collection

for std in STANDARDS_TO_REINGEST:
    info = AVAILABLE_STANDARDS[std]
    pdf_path = f"data/{info['pdf_filename']}"
    cache_path = f"data/{info['cache_filename']}"
    textbook_id = info['textbook_id']
    
    print(f"\n{'='*60}")
    print(f"Re-ingesting Standard {std} — {info['name']}")
    print('='*60)
    
    # Step 1: Delete existing chunks for this standard
    print(f"  Deleting existing Std {std} chunks...")
    try:
        existing = col.get(where={"standard": std})
        if existing and existing["ids"]:
            col.delete(ids=existing["ids"])
            print(f"  Deleted {len(existing['ids'])} existing chunks")
        else:
            print(f"  No existing chunks found")
    except Exception as e:
        print(f"  Warning during delete: {e}")
    
    # Step 2: Load from OCR cache
    print(f"  Loading OCR cache from {cache_path}...")
    loader = PDFLoaderOCR(pdf_path=pdf_path, standard=std)
    pages = loader.load(cache_path=cache_path)
    print(f"  Loaded {len(pages)} pages")
    
    # Step 3: Clean
    print(f"  Cleaning text...")
    cleaner = TextCleaner()
    cleaned_pages = cleaner.clean(pages)
    print(f"  Cleaned: {len(cleaned_pages)} pages")
    
    # Step 4: Chunk with correct chapter metadata
    print(f"  Chunking with corrected chapter maps...")
    chunker = TextChunker()
    chunks = chunker.chunk_pages(
        pages=cleaned_pages,
        source_filename=info['pdf_filename'],
        standard=std,
        textbook_id=textbook_id,
    )
    print(f"  Created {len(chunks)} chunks")
    
    # Verify chapter distribution
    from collections import Counter
    chapters = Counter(c.metadata.get('chapter', 'unknown') for c in chunks)
    print(f"  Unique chapters: {len(chapters)}")
    for ch, count in chapters.most_common(5):
        print(f"    [{count:3d}] {ch}")
    
    # Step 5: Add to ChromaDB
    print(f"  Adding to ChromaDB...")
    chroma.add_documents(chunks)
    print(f"  ✅ Standard {std} re-ingested successfully!")

# Verify total count
total = col.count()
print(f"\n{'='*60}")
print(f"✅ Re-ingestion complete. Total chunks in DB: {total}")
print(f"{'='*60}")

# Per-standard verification
print("\nPer-standard verification:")
for std in [6, 7, 8, 9, 10]:
    try:
        res = col.get(where={"standard": std})
        count = len(res["ids"]) if res and "ids" in res else 0
        print(f"  Std {std}: {count} chunks")
    except Exception as e:
        print(f"  Std {std}: ERROR - {e}")
