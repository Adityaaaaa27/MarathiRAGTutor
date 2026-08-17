"""
Quick verification of Std 6 RAG pipeline after purge.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

from app.services.query_service import QueryService

svc = QueryService()
svc.initialize()

TESTS = [
    "‘निसर्गरम्य माथेरान’ या पाठात माथेरानचे वर्णन कसे केले आहे?",
    "‘चिमणीचं घरटं’ या पाठाचा मुख्य सारांश काय आहे?",
    "‘या भारतात बंधुभाव’ या प्रार्थनेचा मुख्य संदेश काय आहे?"
]

for q in TESTS:
    print(f"\n[Q]: {q}")
    res = svc.ask(question=q, standard=6)
    print(f"Pages: {res.page_numbers}")
    print(f"Answer: {res.answer[:250].replace(chr(10), ' ')}...")
