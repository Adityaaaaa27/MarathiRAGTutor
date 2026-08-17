# 📘 Marathi & Indic PDF RAG Pipeline Playbook
### *High-Accuracy Text Extraction, Vision OCR, Ingestion & RAG Strategy for Legacy-Encoded Indic Documents*

---

## 📌 1. The Core Problem: Legacy DTP Font Encoding

Many Indian government textbooks, state board PDFs (Balbharati, NCERT), and regional legal documents were created using legacy DTP typesetting fonts (e.g., `BalBharati01`, `BalBharati02`, `Shree-Dev`, `APS-DV`, `Akruti`, `DV-TTSurekh`).

### Why standard PDF extraction fails:
* **Standard Extractors (PyMuPDF, pdfplumber, pypdf, Tesseract without trained font models):** Read raw bytecodes that map font glyphs to ASCII/Latin characters rather than standard Devanagari Unicode (UTF-8).
* **Result:** Direct extraction yields garbled text like `8` for `श`, `7` for `व`, `ƈ` for `क`, or broken matras (e.g. `१. या भारतात बंधुभाव विनात येऊ द्या देव विविधांचा असा द्या...`).
* **Conclusion:** Regex conversion alone is brittle and incomplete across hundreds of pages. **High-resolution Vision OCR via Multimodal LLMs (Mistral Pixtral-12B / Gemini Vision) is the most robust, production-grade solution.**

---

## 🏗️ 2. End-to-End Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ 1. PDF Document (Legacy BalBharati / Indic Non-Unicode PDF) │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. PyMuPDF In-Memory Page Rendering                         │
│    - Render at 300 DPI (Matrix 300/72)                      │
│    - Convert to PNG bytes in-memory (No temp disk files)    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. JSON Sidecar Cache Check (`*_ocr_cache.json`)            │
│    - If page in cache: Return instant cached text (0 cost)  │
│    - If not in cache: Send to Vision OCR API                │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Multimodal Vision OCR (Mistral Pixtral-12B / Gemini)     │
│    - Extract pure Devanagari Unicode preserving structure   │
│    - Save page OCR output to cache JSON incrementally       │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Text Cleaning & Normalization                            │
│    - Standardize Dandas (। / ॥), quotes, and whitespace     │
│    - Strip duplicate boilerplate headers / footers          │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Context-Enriched Chunking                                │
│    - RecursiveCharacterTextSplitter (chunk_size=800, ol=150)│
│    - Tag with [Chapter Title | पृष्ठ: X] Header             │
│    - Inject synthetic/extracted Table of Contents chunks    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Multilingual Embeddings & Vector Database                │
│    - sentence-transformers/paraphrase-multilingual-MiniLM-L12│
│    - Persist to ChromaDB with metadata filters              │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. RAG Query Engine with Smart Intent Routing               │
│    - TOC Query Detection: Priority retrieval of full TOC    │
│    - Chapter-Aware Retrieval: Targeted filtering by chapter │
│    - Clean Output: Strip citation/page noise for user       │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ 3. Implementation Blueprint

### Step 3.1: Environment Configuration (`.env`)

```ini
# Mistral API Key (for Pixtral Vision OCR & LLM Generation)
MISTRAL_API_KEY=your_mistral_api_key_here

# (Optional) Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Hugging Face Embeddings Configuration
EMBEDDING_MODE=local
EMBEDDING_MODEL_NAME=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# Storage & Retrieval Settings
RETRIEVER_TOP_K=10
CHUNK_SIZE=800
CHUNK_OVERLAP=150
```

---

### Step 3.2: Reusable Vision OCR PDF Loader (`pdf_loader_ocr.py`)

This loader renders PDF pages into 300-DPI PNGs, performs OCR via Mistral Pixtral-12B, and caches every page to a JSON file.

```python
import base64
import json
import os
import time
from pathlib import Path
from typing import Optional
import pymupdf  # PyMuPDF
from mistralai import Mistral
from pydantic import BaseModel, Field

class PageContent(BaseModel):
    page_number: int
    text: str
    char_count: int
    is_empty: bool = False
    error: Optional[str] = None

class ExtractionResult(BaseModel):
    source: str
    total_pages: int = 0
    extracted_pages: int = 0
    empty_pages: int = 0
    failed_pages: int = 0
    pages: list[PageContent] = []

class VisionOCRPDFLoader:
    # Pages to skip (covers, copyright, blanks)
    SKIP_PAGES: set[int] = {1, 2, 6, 99, 100}

    _OCR_PROMPT = (
        "This is a page from an Indian state board regional textbook. "
        "Please extract ALL text from this image accurately in proper Marathi / Devanagari Unicode. "
        "Preserve the original structure: headings, stanzas, paragraphs, and numbered lists. "
        "Do NOT translate. Do NOT add explanations. Output ONLY the extracted text. "
        "If the page is blank, an image, or has no readable text, output exactly: [BLANK PAGE]"
    )

    def __init__(self, dpi: int = 300, use_cache: bool = True):
        self._dpi = dpi
        self._use_cache = use_cache
        self._client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

    def _render_page_as_png(self, page: pymupdf.Page) -> bytes:
        mat = pymupdf.Matrix(self._dpi / 72, self._dpi / 72)
        pix = page.get_pixmap(matrix=mat, colorspace=pymupdf.csRGB)
        return pix.tobytes("png")

    def _ocr_page(self, png_bytes: bytes, page_num: int) -> str:
        b64 = base64.b64encode(png_bytes).decode()
        for attempt in range(3):
            try:
                response = self._client.chat.complete(
                    model="pixtral-12b-2409",
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                            {"type": "text", "text": self._OCR_PROMPT},
                        ],
                    }],
                )
                text = response.choices[0].message.content.strip()
                return "" if text == "[BLANK PAGE]" else text
            except Exception as exc:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                else:
                    raise

    def load(self, pdf_path: Path) -> ExtractionResult:
        cache_path = pdf_path.parent / f"{pdf_path.stem}_ocr_cache.json"
        cache = {}
        if self._use_cache and cache_path.exists():
            cache = json.loads(cache_path.read_text(encoding="utf-8"))

        doc = pymupdf.open(str(pdf_path))
        result = ExtractionResult(source=str(pdf_path), total_pages=len(doc))

        for idx in range(len(doc)):
            page_num = idx + 1
            if page_num in self.SKIP_PAGES:
                result.empty_pages += 1
                result.pages.append(PageContent(page_number=page_num, text="", char_count=0, is_empty=True))
                continue

            if self._use_cache and str(page_num) in cache:
                text = cache[str(page_num)]
            else:
                page = doc.load_page(idx)
                png_bytes = self._render_page_as_png(page)
                text = self._ocr_page(png_bytes, page_num)
                if self._use_cache:
                    cache[str(page_num)] = text
                    cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

            if len(text.strip()) < 5:
                result.empty_pages += 1
                result.pages.append(PageContent(page_number=page_num, text="", char_count=0, is_empty=True))
            else:
                result.extracted_pages += 1
                result.pages.append(PageContent(page_number=page_num, text=text, char_count=len(text)))

        doc.close()
        return result
```

---

### Step 3.3: Context-Enriched Text Chunking

Every chunk should carry its parent chapter name and page number directly inside `page_content` to enhance embedding similarity matching:

```python
# Format each chunk before storing in vector database:
enriched_text = f"[{chapter_name} | पृष्ठ: {page_number}]\n{chunk_text}"
```

---

### Step 3.4: Table of Contents (TOC) & Chapter Intent Routing

To prevent the model from hallucinating or retrieving random exercise pages when asked broad questions like *"List all lessons from 1 to 20"*:

```python
TOC_KEYWORDS = [
    "अनुक्रमणिका", "विषयसूची", "विषय सूची", "सर्व पाठ", "सर्व कविता", "सर्व धडे",
    "धड्यांची यादी", "पाठांची यादी", "कवितांची यादी", "सर्व विषय", "कोणकोणते धडे",
    "कोणकोणते पाठ", "कोणत्या कविता", "१ ते २०", "१ ते 20", "1 ते 20", "1 to 20",
    "पुस्तकातील सर्व", "पाठ्यपुस्तकातील सर्व", "धडे आणि कविता", "पाठ आणि कविता",
    "table of contents", "chapters list", "all lessons", "all chapters", "all poems",
]

def is_toc_query(query: str) -> bool:
    cleaned = re.sub(r"[‘'“”\"’]", "", query).strip().lower()
    return any(kw in cleaned for kw in TOC_KEYWORDS)

# In retrieval:
if is_toc_query(query):
    # Retrieve page 10 (Table of Contents) and synthetic TOC metadata chunks first
    toc_results = chroma_service.search(query="अनुक्रमणिका सर्व पाठ", filter_dict={"chapter": "table_of_contents"})
    p10_results = chroma_service.search(query="अनुक्रमणिका", filter_dict={"chapter": "अनुक्रमणिका"})
    general_results = chroma_service.search(query=query)
    context_chunks = deduplicate(toc_results + p10_results + general_results)
```

---

## 📋 4. Step-by-Step Execution Playbook for Any New PDF

Follow these exact steps when adding a new Marathi / regional language textbook or document:

### Step 1: Place PDF in Data Folder
Put the target file in `data/<book_name>.pdf`.

### Step 2: Run a Single-Page Diagnostic Test
Verify OCR quality on 1 sample page:
```bash
python -c "
import pymupdf, base64, os
from dotenv import load_dotenv; load_dotenv()
from mistralai import Mistral
client = Mistral(api_key=os.getenv('MISTRAL_API_KEY'))
doc = pymupdf.open('data/<book_name>.pdf')
pix = doc[10].get_pixmap(matrix=pymupdf.Matrix(300/72, 300/72))
b64 = base64.b64encode(pix.tobytes('png')).decode()
resp = client.chat.complete(
    model='pixtral-12b-2409',
    messages=[{'role':'user','content':[{'type':'image_url','image_url':{'url':f'data:image/png;base64,{b64}'}},{'type':'text','text':'Extract all Marathi text verbatim in Devanagari Unicode.'}]}]
)
print(resp.choices[0].message.content)
"
```

### Step 3: Run Full Ingestion
```bash
# Delete old Chroma index and execute fresh ingestion
Remove-Item -Recurse -Force "chroma" -ErrorAction SilentlyContinue
python -m app.cli.ingest
```
* The first run will process all pages via Vision OCR and automatically create `data/<book_name>_ocr_cache.json`.
* All subsequent re-indexes are **instant** (loads straight from JSON cache in ~20 seconds).

### Step 4: Verify RAG Output
Run test queries across poems, prose stories, and TOC:
```bash
python -c "
from app.services.query_service import QueryService
qs = QueryService(); qs.initialize()
print(qs.ask('१ ते २० पर्यंतचे सर्व विषय').answer)
"
```

### Step 5: Start Web UI
```bash
python -m app.cli.web
```
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

---

## 💡 5. Best Practices & Key Takeaways

1. **Never rely on raw PDF text extraction for legacy Indic fonts:** Always use 300-DPI rasterization + Vision LLM OCR.
2. **Always use sidecar JSON caching:** API calls happen once per page; re-runs and debugging never consume extra API quota.
3. **Prefix all chunks with section context:** `[Chapter Title | पृष्ठ: X]` prevents vector search from losing chapter context.
4. **Implement TOC query routing:** Broad curriculum questions need Table of Contents prioritization to avoid retrieving random exercises.
5. **Enforce clean user responses:** Keep citations, chunk identifiers, and raw page dumps in internal logs, presenting the student with clean, natural Marathi answers.
