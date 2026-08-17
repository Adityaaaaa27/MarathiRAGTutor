"""
Test cross-standard refusal & isolation without hitting rate limits.
"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

from app.services.query_service import QueryService

qs = QueryService()
qs.initialize()

print("\n--- Testing Cross-Standard Refusal / Isolation ---")
print("Selected Standard: 7")
print("Question: स्टीफन हॉकिंग यांच्याबद्दल काय माहिती दिली आहे? (Std 8 topic)")

time.sleep(2) # avoid 429
res = qs.ask(question="स्टीफन हॉकिंग यांच्याबद्दल काय माहिती दिली आहे?", standard=7)

print(f"\nRetrieved {len(res.retrieved_chunks)} chunks.")
for c in res.retrieved_chunks[:3]:
    print(f"  Chunk chapter: {c.chapter} | Page: {c.page_number}")

print(f"\nAnswer:\n{res.answer}")
