"""
Purge all chunks from ChromaDB except Standard 6.
Verify that only Standard 6 remains intact.
"""
import sys
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

print(f"Total documents before purge: {col.count()}")

# Delete all chunks where standard != 6 (or standard in [7, 8, 9, 10])
for std in [7, 8, 9, 10]:
    try:
        res = col.get(where={"standard": std})
        if res and res.get("ids"):
            print(f"Deleting {len(res['ids'])} chunks for Standard {std}...")
            col.delete(ids=res["ids"])
            print(f"Standard {std} deleted.")
        else:
            print(f"No chunks found for Standard {std}.")
    except Exception as e:
        print(f"Error checking/deleting standard {std}: {e}")

print(f"\nTotal documents after purge: {col.count()}")

# Verify Std 6 chunks
res6 = col.get(where={"standard": 6})
print(f"Standard 6 chunk count: {len(res6['ids'])}")
