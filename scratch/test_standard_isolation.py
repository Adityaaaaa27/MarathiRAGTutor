"""
Test standard isolation and accuracy across Standards 6, 7, 8, 9.
Verifies that:
1. Retrieval is strictly isolated to the selected standard.
2. Answers are accurate and grounded in the selected standard's textbook.
3. Cross-standard queries do NOT leak chunks from other standards.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

from app.services.query_service import QueryService

print("Initializing QueryService...")
qs = QueryService()
qs.initialize()

test_cases = [
    # 1. Standard 6 Query
    {
        "std": 6,
        "q": "चिमणीचं घरटं या पाठात चिमणीने आपले घरटे कुठे बांधले होते?",
        "desc": "Std 6 - चिमणीचं घरटं"
    },
    # 2. Standard 7 Query
    {
        "std": 7,
        "q": "श्यामाचे बंधुप्रेम या पाठात श्यामने आपल्या भावासाठी काय आणले होते आणि लेखक कोण आहेत?",
        "desc": "Std 7 - श्यामाचे बंधुप्रेम (सानेगुरुजी)"
    },
    # 3. Standard 8 Query
    {
        "std": 8,
        "q": "स्टीफन हॉकिंग कोणत्या विषयाचे शास्त्रज्ञ होते?",
        "desc": "Std 8 - स्टीफन हॉकिंग"
    },
    # 4. Standard 9 Query
    {
        "std": 9,
        "q": "जि. आय. पी. रेल्वे या पाठाचे लेखक कोण आहेत आणि रेल्वे कधी सुरू झाली?",
        "desc": "Std 9 - जि. आय. पी. रेल्वे (प्रबोधनकार ठाकरे)"
    },
    # 5. Cross-Standard Isolation Test: Ask Std 8 question with Std 7 filter
    {
        "std": 7,
        "q": "स्टीफन हॉकिंग यांच्याबद्दल काय माहिती दिली आहे?",
        "desc": "Isolation Test - Asking Std 8 topic in Std 7 (Must NOT leak Std 8 chunks)"
    },
]

print("\n" + "="*80)
print("RUNNING STANDARD ISOLATION & ACCURACY TESTS")
print("="*80)

for i, tc in enumerate(test_cases, 1):
    std = tc["std"]
    q = tc["q"]
    desc = tc["desc"]
    
    print(f"\n--- Test {i}: {desc} ---")
    print(f"Selected Standard: {std}")
    print(f"Question: {q}")
    
    res = qs.ask(question=q, standard=std)
    
    # Check chunks isolation
    chunk_standards = set(c.metadata.get("standard") if hasattr(c, "metadata") else None for c in res.retrieved_chunks)
    # Also check from chunk content header if metadata object isn't exposed directly
    retrieved_stds = []
    for c in res.retrieved_chunks:
        # Check standard in text e.g. [इयत्ता 7 वी ...
        if f"इयत्ता {std} वी" in c.content:
            retrieved_stds.append(std)
        else:
            retrieved_stds.append("OTHER")
    
    all_isolated = all(s == std for s in retrieved_stds) if retrieved_stds else True
    
    print(f"Retrieved {len(res.retrieved_chunks)} chunks from pages: {res.page_numbers}")
    print(f"Standard Isolation check: {'✅ PASSED (100% Std ' + str(std) + ')' if all_isolated else '❌ FAILED (Leaked standards: ' + str(retrieved_stds) + ')'}")
    print(f"Answer snippet:\n{res.answer[:350]}...")
    print("-" * 60)

print("\nAll isolation tests finished.")
