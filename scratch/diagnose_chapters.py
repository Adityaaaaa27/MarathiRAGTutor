import sys
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

from app.vectorstore.chroma_service import ChromaService
from app.embeddings.embedding_service import EmbeddingService

emb = EmbeddingService()
emb.initialize()
chroma = ChromaService(embedding_service=emb)
chroma.create()

col = chroma._vectorstore._collection

# For each standard, check unique chapters and sample good/bad text
for std in [7, 8, 9, 10]:
    print(f"\n{'='*60}")
    print(f"STD {std} - Chapter Distribution & Content Quality")
    print('='*60)
    res = col.get(where={"standard": std})
    
    # Count per chapter
    from collections import Counter
    chapters = Counter(m['chapter'] for m in res['metadatas'])
    print(f"Unique chapters: {len(chapters)}")
    for chap, count in chapters.most_common(10):
        print(f"  [{count:3d}] {chap}")
    
    # Find a page that has actual chapter content (not page 1-5)
    good_samples = [(res['documents'][i], res['metadatas'][i]) 
                    for i in range(len(res['documents'])) 
                    if res['metadatas'][i].get('page_number', 0) > 8]
    
    if good_samples:
        doc, meta = good_samples[0]
        print(f"\nSample content (page {meta.get('page_number')}):")
        print(doc[:300])
    
    # Check for garbled text
    garbled = [d for d in res['documents'] if '[B' in d and 'PAGE' in d]
    print(f"\nGarbled OCR entries: {len(garbled)}")
