"""
Quick test: OCR a single page of the textbook with Gemini Vision.
Run: python test_ocr_single_page.py
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
os.chdir(r"c:\Users\USER\Desktop\NLP\marathi-rag")
sys.path.insert(0, r"c:\Users\USER\Desktop\NLP\marathi-rag")

from dotenv import load_dotenv
load_dotenv()

import pymupdf
import base64
import google.genai as genai
import google.genai.types as genai_types

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ ERROR: GEMINI_API_KEY not found in .env")
    print("  Add this line to your .env file:")
    print("  GEMINI_API_KEY=your_key_here")
    print("  Get a free key: https://aistudio.google.com/app/apikey")
    sys.exit(1)

client = genai.Client(api_key=api_key)

doc = pymupdf.open("data/textbook.pdf")

# Test page 11 (the 'या भारतात बंधुभाव' poem)
page_num = 11
page = doc[page_num - 1]
mat = pymupdf.Matrix(300 / 72, 300 / 72)
pix = page.get_pixmap(matrix=mat, colorspace=pymupdf.csRGB)
png_bytes = pix.tobytes("png")

print(f"Rendering page {page_num}... ({len(png_bytes)} bytes)")

prompt = (
    "This is a page from a Maharashtra state Balbharati Marathi textbook for Standard 6. "
    "Please extract ALL text from this image accurately in proper Marathi Devanagari Unicode. "
    "Preserve the original structure: headings, stanzas, paragraphs, and numbered lists. "
    "Do NOT translate. Do NOT add explanations. Output ONLY the extracted Marathi text. "
    "If the page is blank, an image, or has no readable text, output exactly: [BLANK PAGE]"
)

response = client.models.generate_content(
    model="gemini-flash-latest",
    contents=[
        genai_types.Part.from_bytes(data=png_bytes, mime_type="image/png"),
        prompt,
    ],
)

print("\n=== OCR RESULT (Page 11) ===")
print(response.text)
print("\n✅ OCR test successful!")
