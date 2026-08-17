import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from app.services.query_service import QueryService

try:
    print("Initializing QueryService...")
    qs = QueryService()
    qs.initialize()
    print("Fetching standards info...")
    info = qs.get_standards_info()
    print("SUCCESS!")
    print(info)
except Exception as e:
    import traceback
    print("ERROR:")
    traceback.print_exc()
