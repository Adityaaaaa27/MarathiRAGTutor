"""
Deep diagnostic: compare chunk quality across all standards.
Shows actual text content of chunks per chapter to spot OCR issues.
"""
import sys, json
from pathlib import Path
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

from app.embeddings.embedding_service import EmbeddingService
from app.vectorstore.chroma_service import ChromaService

emb = EmbeddingService()
emb.initialize()
chroma = ChromaService(embedding_service=emb)
chroma.create()
col = chroma._vectorstore._collection

STANDARDS_TO_CHECK = [7, 8, 9]

for std in STANDARDS_TO_CHECK:
    print(f"\n{'='*70}")
    print(f"STANDARD {std} — Detailed Chapter Quality Check")
    print('='*70)

    res = col.get(where={"standard": std}, include=["metadatas", "documents"])
    docs = res["documents"]
    metas = res["metadatas"]
    
    # Group by chapter
    by_chapter = defaultdict(list)
    for doc, meta in zip(docs, metas):
        chapter = meta.get("chapter", "unknown")
        by_chapter[chapter].append({"doc": doc, "page": meta.get("page_number", "?")})
    
    print(f"Total chunks: {len(docs)} | Unique chapters: {len(by_chapter)}")
    print()
    
    for chapter, chunks in sorted(by_chapter.items(), key=lambda x: x[0]):
        pages = sorted(set(c["page"] for c in chunks))
        # Show first 200 chars of first chunk to check OCR quality
        sample_text = chunks[0]["doc"][:250].replace("\n", " ")
        print(f"  📗 [{len(chunks):2d} chunks | pages {pages}]")
        print(f"     Chapter: {chapter}")
        print(f"     Sample : {sample_text}")
        print()
