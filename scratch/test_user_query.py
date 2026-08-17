"""
Test the exact query that failed for the user:
'बेटा, मी एकटो आहे!' या पाठात तिसरी घंटा घणघणल्यानंतर काय झाले?
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

from app.services.query_service import QueryService

svc = QueryService()
svc.initialize()

question = "'बेटा, मी एकटो आहे!' या पाठात तिसरी घंटा घणघणल्यानंतर काय झाले?"
print(f"\nAsking: {question}")

result = svc.ask(question=question, standard=9)
print(f"\nPages retrieved: {result.page_numbers}")
print(f"Chunks retrieved: {len(result.retrieved_chunks)}")
print("\n--- Answer ---")
print(result.answer)
