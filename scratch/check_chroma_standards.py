import sys
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

from app.vectorstore.chroma_service import ChromaService
from app.embeddings.embedding_service import EmbeddingService

print("Initializing embeddings...")
emb = EmbeddingService()
emb.initialize()

print("Connecting to ChromaDB...")
chroma = ChromaService(embedding_service=emb)
chroma.create()

# Total count
col = chroma._vectorstore._collection
total = col.count()
print(f"\nTotal documents in DB: {total}")

# Per standard count
print("\nPer-standard chunk counts:")
for std in [6, 7, 8, 9, 10]:
    try:
        res = col.get(where={"standard": std})
        count = len(res["ids"]) if res and "ids" in res else 0
        print(f"  Std {std}: {count} chunks")
        # Show sample metadata
        if count > 0:
            meta = res["metadatas"][0]
            doc_text = res["documents"][0][:100].replace('\n',' ')
            print(f"    Sample metadata: {meta}")
            print(f"    Sample text: {doc_text}")
    except Exception as e:
        print(f"  Std {std}: ERROR - {e}")
