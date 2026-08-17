"""Test Mistral pixtral-12b Vision OCR on page 11."""
import sys, os, base64
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
os.chdir(r"c:\Users\USER\Desktop\NLP\marathi-rag")

from dotenv import load_dotenv
load_dotenv()

import pymupdf
from mistralai import Mistral

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

doc = pymupdf.open("data/textbook.pdf")
page = doc[10]  # page 11
mat = pymupdf.Matrix(300 / 72, 300 / 72)
pix = page.get_pixmap(matrix=mat, colorspace=pymupdf.csRGB)
png_bytes = pix.tobytes("png")
b64 = base64.b64encode(png_bytes).decode()

print(f"Rendering page 11... ({len(png_bytes)} bytes)")

prompt = (
    "This is a page from a Maharashtra state Balbharati Marathi textbook for Standard 6. "
    "Please extract ALL text from this image accurately in proper Marathi Devanagari Unicode. "
    "Preserve the original structure: headings, stanzas, paragraphs, and numbered lists. "
    "Do NOT translate. Do NOT add explanations. Output ONLY the extracted Marathi text. "
    "If the page is blank, an image, or has no readable text, output exactly: [BLANK PAGE]"
)

response = client.chat.complete(
    model="pixtral-12b-2409",
    messages=[{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
            {"type": "text", "text": prompt},
        ],
    }],
)

print("\n=== OCR RESULT (Page 11 via Mistral pixtral-12b) ===")
print(response.choices[0].message.content)
print("\n✅ Mistral Vision OCR test done!")
