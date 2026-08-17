import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from app.services.query_service import QueryService

try:
    print("Initializing QueryService...")
    qs = QueryService()
    qs.initialize()
    
    questions = [
        # Standard 6
        ("या भारतात बंधुभाव प्रार्थनेचा मुख्य संदेश काय आहे?", 6),
        # Standard 7
        ("इयत्ता ७ वी च्या पुस्तकातील प्रमुख पाठांची नावे सांगा.", 7),
        # Standard 9
        ("‘बेटा, मी एकतो आहे!’ या पाठात तिसरी घंटा घणघणल्यानंतर काय झाले?", 9),
        # Standard 10
        ("इयत्ता १० वी च्या संतवाणीमधील संदेश काय आहे?", 10),
    ]
    
    for q, std in questions:
        print("\n" + "="*50)
        print(f"QUESTION (Std {std}): {q}")
        print("="*50)
        res = qs.ask(question=q, standard=std)
        print(f"ANSWER:\n{res.answer}")
        print(f"SOURCES: Pages {res.page_numbers} from {res.source}")
        
except Exception as e:
    import traceback
    traceback.print_exc()
