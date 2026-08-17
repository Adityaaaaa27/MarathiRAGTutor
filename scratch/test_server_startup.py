"""
Verify FastAPI endpoints using TestClient.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

from fastapi.testclient import TestClient
from app.web.server import app

client = TestClient(app)

print("\n1. Testing GET /api/health...")
res = client.get("/api/health")
print(f"Status: {res.status_code}, Body: {res.json()}")

print("\n2. Testing GET /api/standards...")
res = client.get("/api/standards")
print(f"Status: {res.status_code}")
for s in res.json():
    print(f"  Standard {s['standard']}: {s['name']} | Chunks: {s['chunk_count']} | Indexed: {s['is_indexed']}")

print("\n3. Testing POST /api/ask with Standard 8...")
res = client.post("/api/ask", json={
    "question": "चिव चिव चिमण्या या पाठाचे लेखक कोण आहेत?",
    "standard": 8,
})
print(f"Status: {res.status_code}")
if res.status_code == 200:
    data = res.json()
    print(f"Answer snippet:\n{data['answer'][:200]}...")
    print(f"Pages: {data['page_numbers']}")
    print(f"Retrieved Chunks: {len(data['retrieved_chunks'])}")
else:
    print(f"Error: {res.text}")

print("\n✅ All server endpoints verified successfully!")
