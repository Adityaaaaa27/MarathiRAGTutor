"""
Comprehensive live query test across all 4 standards.
Tests real RAG answers via the QueryService, just like the web UI does.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

from app.services.query_service import QueryService

svc = QueryService()
svc.initialize()

TESTS = [
    # (standard, question, expected_keywords)
    (6, "माथेरान हे कसे ठिकाण आहे?", ["थंड", "निसर्ग", "माथेरान"]),
    (6, "चिमणीचं घरटं या पाठात काय घडते?", ["चिमणी", "घरटं", "ईशा"]),
    (7, "श्यामाचे बंधुप्रेम या पाठाचे लेखक कोण आहेत?", ["सानेगुरुजी", "साने"]),
    (7, "टप् टप् पडती ही कविता कोणी लिहिली?", ["पाडगावकर", "मंगेश"]),
    (7, "आजारी पडण्याचा प्रयोग या पाठात काय आहे?", ["मिरासदार", "आजारी"]),
    (8, "विजय तेंडुलकर यांनी कोणता पाठ लिहिला?", ["चिव चिव चिमण्या", "तेंडुलकर"]),
    (8, "स्टीफन हॉकिंग कोण होते?", ["शास्त्रज्ञ", "हॉकिंग"]),
    (8, "ध्येयपूर्तीचा ध्यास या पाठाचे लेखक कोण?", ["लक्ष्मण लोंढे", "लोंढे"]),
    (9, "वि.पु. काळे यांनी लिहिलेला पाठ कोणता?", ["बेटा", "एकटो", "काळे"]),
    (9, "मनाचे श्लोक कोणी लिहिले?", ["समर्थ रामदास", "रामदास"]),
    (9, "सुधा मूर्ती यांनी कोणता पाठ लिहिला?", ["दिव्याची ज्योत", "मूर्ती"]),
]

print(f"\n{'='*70}")
print("LIVE RAG QUALITY TEST — All Standards")
print('='*70)

passed = 0
failed = 0
errors = 0

for std, question, expected in TESTS:
    print(f"\n[STD {std}] Q: {question}")
    try:
        result = svc.ask(question=question, standard=std)
        answer = result.answer
        # Check if expected keywords are present
        found_keywords = [k for k in expected if k in answer]
        status = "✅ PASS" if found_keywords else "❌ FAIL"
        
        print(f"  Status  : {status}")
        print(f"  Keywords: expected={expected}, found={found_keywords}")
        print(f"  Answer  : {answer[:300].replace(chr(10), ' ')}")
        
        if found_keywords:
            passed += 1
        else:
            failed += 1
    except Exception as e:
        print(f"  Status  : 💥 ERROR — {e}")
        errors += 1

print(f"\n{'='*70}")
print(f"SUMMARY: {passed} passed / {failed} failed / {errors} errors out of {len(TESTS)} tests")
print('='*70)
