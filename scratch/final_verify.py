"""
Final targeted verification — one question per standard with delays.
Tests both retrieval quality and TOC queries.
"""
import sys
import time
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

from app.services.query_service import QueryService

svc = QueryService()
svc.initialize()

TESTS = [
    # (standard, question, desc)
    (6, "माथेरान या ठिकाणाचे वर्णन करा.",                   "Std 6 - Chapter retrieval"),
    (7, "सानेगुरुजी यांच्या पाठाचा सारांश सांगा.",          "Std 7 - Author-based lookup"),
    (8, "स्टीफन हॉकिंग कोण होते?",                          "Std 8 - Scientist chapter"),
    (9, "दिव्याची ज्योत या पाठात सुधा मूर्ती काय सांगतात?",  "Std 9 - Specific chapter"),
    # TOC queries for each standard
    (7, "इयत्ता ७ वी च्या पुस्तकातील सर्व पाठांची यादी द्या.", "Std 7 - TOC query"),
    (9, "इयत्ता ९ वी मधील सर्व कवितांची नावे सांगा.",          "Std 9 - TOC query"),
    # Cross-standard isolation check
    (7, "माथेरानचे वर्णन सांगा.",                             "Std 7 - Std6 topic (should refuse or find nothing relevant)"),
]

print(f"\n{'='*70}")
print("FINAL VERIFICATION — RAG Quality Check")
print('='*70)

passed = 0
total = 0

for std, question, desc in TESTS:
    total += 1
    print(f"\n[{desc}]")
    print(f"  Q: {question}")
    try:
        result = svc.ask(question=question, standard=std)
        answer = result.answer
        pages = result.page_numbers
        chunks = len(result.retrieved_chunks)
        print(f"  ✅ Answer ({chunks} chunks, pages {pages}):")
        print(f"     {answer[:350].replace(chr(10), ' ')}")
        passed += 1
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
    
    print(f"  Waiting 8s to avoid rate limit...")
    time.sleep(8)

print(f"\n{'='*70}")
print(f"RESULT: {passed}/{total} queries succeeded")
print('='*70)
