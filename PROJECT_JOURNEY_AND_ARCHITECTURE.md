# 📘 Marathi RAG Tutor — Complete Project Journey, Architecture & Technical Deep-Dive

---

## 🌟 1. Executive Summary & Core Mission

### The Problem We Set Out to Solve
In Maharashtra, millions of school students from Standards 6, 7, and 8 study their mother tongue using the state board **Balbharti (बालभारती)** curriculum. When studying at home or preparing for exams, students and parents face real challenges:
1. **Lack of Instant, Authentic Doubt-Solving**: Students often have questions about specific poems (*कविता*), lessons (*पाठ*), word meanings (*शब्दार्थ*), or author backgrounds.
2. **Generic LLM Hallucinations**: Standard AI models (like generic ChatGPT) pull information from across the internet, mix up different state curriculums, invent moral lessons that are not in the book, or use overly formal/Sanskritized Marathi that middle-school students cannot comprehend.
3. **The "Marathlish" Reality**: Real school students rarely type in pure Devanagari script. They type phonetically using English keyboards (e.g., *"mla ya pathachi summary pahije"* or *"Matheran baddal kay sangitle ahe?"*). Standard search and vector systems fail completely when matching Roman English queries against Devanagari textbook text.

### Our Solution
We engineered a **Production-Quality Retrieval-Augmented Generation (RAG) AI Tutor System** tailored specifically for the Maharashtra State Board Balbharti syllabus.
- **100% Grounded in Textbook**: Strict zero-hallucination policy. The AI answers solely based on verified textbook pages and provides exact page references.
- **Multilingual Query Understanding**: Students can ask in Devanagari Marathi, English, or phonetically Romanized Marathi ("Marathlish").
- **Multi-Standard Support**: Partitioned knowledge bases for Standard 6, Standard 7, and Standard 8.

---

## 🧭 2. Architectural Blueprint

Below is the end-to-end pipeline showing how a student's query flows through the entire system:

```
+-----------------------------------------------------------------------------------+
|                                  USER / STUDENT                                   |
|       Types: "chimanich gharte ya pathat Isha baddal kay sangitle ahe?"           |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                                FASTAPI WEB SERVER                                 |
|                         (Endpoint: POST /api/ask)                                 |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                          TRANSLITERATION SERVICE                                  |
|   - Detects script & phonetics                                                    |
|   - Converts: "चिमाणीचे घरटे या पाठात ईशाबद्दल काय सांगितले आहे?"              |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                          EMBEDDING SERVICE (bge-m3)                               |
|   - Generates 1024-dimensional dense semantic vector for the query                |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        CHROMADB VECTOR DATABASE                                   |
|   - Filters by metadata (e.g., standard: "6")                                     |
|   - Cosine similarity search retrieves Top-K most relevant textbook chunks        |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                            RAG PROMPT SERVICE                                     |
|   - Injects retrieved textbook context + Marathi pedagogical teacher persona      |
|   - Enforces strict anti-hallucination and grade-appropriate language rules       |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                            MISTRAL AI (LLM)                                       |
|   - Generates structured, helpful, warm Marathi answer with page citations        |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                              MODERN FRONTEND UI                                   |
|   - Displays clean chat bubble with transliteration badge & formatted Markdown    |
+-----------------------------------------------------------------------------------+
```

---

## 🛠️ 3. Why We Chose This Specific Tech Stack

Every technology in this project was selected after evaluating performance on **Indic language NLP (specifically Marathi/Devanagari)**:

| Component | Technology | Why Chosen Over Alternatives |
| :--- | :--- | :--- |
| **Language** | **Python 3.10+** | Industry standard for AI, LangChain, PyTorch, and NLP libraries. |
| **LLM Engine** | **Mistral AI (`mistral-large-latest`)** | Superior multilingual reasoning, native support for Indic tokenization without heavy character inflation, high fidelity in following system constraints. |
| **Embeddings** | **BAAI/bge-m3** | Leading 1024-dim dense multilingual embedding model with 8192-token context window. Outperforms older English-centric models like OpenAI `text-embedding-ada-002` on Devanagari semantic matching. |
| **Vector DB** | **ChromaDB (Persistent)** | Embeddable, zero-cloud dependency, blazing fast local cosine search, native support for metadata filtering (`where={"standard": "6"}`). |
| **PDF Ingestion** | **PyMuPDF + Vision OCR** | PyMuPDF extracts raw text at high speed. For scanned/complex layout pages, Vision OCR extracts clean Unicode without breaking conjunct letters (*जोडाक्षरे*). |
| **Pipeline Framework**| **LangChain (LCEL)** | Declarative, modular LangChain Expression Language allowing composable, testable, and maintainable pipelines. |
| **Backend API** | **FastAPI + Uvicorn** | Asynchronous, lightning-fast request handling with native Pydantic type validation and automatic OpenAPI docs. |
| **Frontend UI** | **Vanilla HTML5, CSS3, JS** | Zero heavyweight dependencies (no React/Node build steps), instant load times, full aesthetic control (inspired by modern minimalist desktop apps). |

---

## 🧗 4. The Journey: How We Started & Difficulties Faced

Building an Indic language RAG system is drastically different from building standard English RAG. Here is the true story of how we built this system step-by-step and the challenges we conquered:

---

### Challenge 1: The Marathi PDF Extraction Problem (Broken Matras & Ligatures)
* **What Happened**: When extracting text directly from official Balbharti PDFs using standard tools, complex Marathi words broke into gibberish. For example, letters like `क्ष`, `ज्ञ`, `त्र`, and vowel signs (*कान, मात्रा, वेलांटी*) were extracted as disconnected Unicode tokens or incorrect ASCII codes.
* **How We Solved It**:
  1. Implemented **Unicode Normalization (NFC)** in `TextCleaner` to fuse decomposed Unicode characters back into clean Devanagari ligatures.
  2. Built a hybrid extraction system: standard text extraction for clean text streams and high-accuracy Vision OCR for scanned/complex pages.
  3. Filtered out repetitive page headers (*"इयत्ता सहावी"*, *"मराठी बालभारती"*), page numbers (*"पृष्ठ १२"*), and publisher notices.

---

### Challenge 2: The Devanagari Chunking Dilemma
* **What Happened**: Standard English text splitters split text on `\n\n`, `.`, or fixed character counts. In Marathi:
  - Sentences end with standard full stops `.` or the traditional Danda `।`.
  - Splitting mid-word or mid-compound-character corrupted the semantic meaning of chunks.
* **How We Solved It**:
  - Engineered a Marathi-aware `RecursiveCharacterTextSplitter` configured with Indic punctuation separators: `["\n\n", "\n", "।", "!", "?", ".", " ", ""]`.
  - Tuned chunk size to **400 characters with 80-character overlap**, which fits typical Marathi story paragraphs and poetry stanzas perfectly.
  - Attached rich metadata to every chunk: `standard`, `chapter_name`, `page_number`, `chunk_id`.

---

### Challenge 3: The "Marathlish" Query Barrier
* **What Happened**: Testing revealed that school students almost never type in Devanagari script on desktop or mobile keyboards. They type:
  > *"Matheran baddal kay mahiti dili ahe?"* (Romanized Marathi)  
  > *"iska matlab kya hai marathi mein"* (Hindi-Marathi mix)  
  > *"lesson 3 summary pahije"* (English-Marathi mix)  
  When these queries were passed directly to ChromaDB, cosine similarity with Devanagari text was near zero, causing retrieval to fail completely.
* **How We Solved It**:
  - Developed a specialized **`TransliterationService`**.
  - Engineered a few-shot system prompt tailored specifically for Maharashtra State Board student vocabulary.
  - Automatically translates/transliterates mixed phonetic queries into clean, standard Balbharti Devanagari before embedding and retrieval.
  - Returns the transliterated query to the frontend as an educational badge so students can see the correct Marathi spelling.

---

### Challenge 4: Anti-Hallucination & Teacher Tone Calibration
* **What Happened**: Default LLM responses were either too technical (explaining grammatical terms from university linguistics) or hallucinating facts that were not in the Balbharti textbook.
* **How We Solved It**:
  - Crafted an authoritative system prompt in `app/prompts/rag_prompt.py`:
    1. **Strict Context Adherence**: Must only answer using the provided textbook snippets.
    2. **Graceful Fallback**: If information is missing, respond honestly: *"या पाठ्यपुस्तकात याबद्दल माहिती उपलब्ध नाही."*
    3. **Pedagogical Persona**: Friendly, encouraging school teacher tone suited for 11-14 year olds.
    4. **Source Transparency**: Always cite page numbers from the textbook.

---

### Challenge 5: Multi-Standard Isolation
* **What Happened**: When a student selected Standard 7 and asked about a lesson, if Standard 6 had a similarly named topic, results from Standard 6 were leaking into the answer.
* **How We Solved It**:
  - Implemented metadata filtering in `ChromaService` and `RetrieverService`:
    ```python
    retriever = vectorstore.as_retriever(
        search_kwargs={
            "k": 5,
            "filter": {"standard": selected_standard}
        }
    )
    ```
  - Partitioned ingestion so every textbook chunk is strictly tagged with its respective grade (`6`, `7`, or `8`).

---

### Challenge 6: UI/UX Transformation & Live Performance
* **What Happened**: The initial prototype was a terminal CLI. Moving to a web interface required high responsiveness, standard selection pills, error-resilient client logic, and an interface suited for students.
* **How We Solved It**:
  - Built a desktop interface with a cream grid background and a dark chat container.
  - Included a prominent Standard selector (इयत्ता ६ वी, ७ वी, ८ वी).
  - Integrated dynamic status indicators, responsive mobile/desktop breakpoints, and cache-busting on static assets.

---

## 📂 5. Directory Structure & Component Responsibilities

```
marathi-rag/
│
├── app/
│   ├── cli/
│   │   ├── ingest.py            # CLI command to index textbook PDFs
│   │   └── query.py             # CLI interactive terminal query tool
│   │
│   ├── config/
│   │   ├── constants.py         # App-wide string constants and defaults
│   │   └── settings.py          # Pydantic environment configuration (.env)
│   │
│   ├── ingestion/
│   │   ├── pdf_loader.py        # PyMuPDF fast text extractor
│   │   └── pdf_loader_ocr.py    # Vision OCR extractor for scanned pages
│   │
│   ├── preprocessing/
│   │   ├── cleaner.py           # Unicode normalizer & noise cleaner
│   │   ├── chunker.py           # Marathi-aware text chunker
│   │   └── transliteration_service.py # Marathlish -> Devanagari converter
│   │
│   ├── embeddings/
│   │   └── embedding_service.py # BAAI/bge-m3 embedding manager
│   │
│   ├── vectorstore/
│   │   └── chroma_service.py    # ChromaDB persistent vector repository
│   │
│   ├── retrieval/
│   │   └── retriever.py         # Standard-filtered similarity retriever
│   │
│   ├── llm/
│   │   └── mistral_service.py   # Mistral AI API integration
│   │
│   ├── prompts/
│   │   └── rag_prompt.py        # Pedagogical Marathi RAG prompt template
│   │
│   ├── chains/
│   │   └── rag_chain.py         # LCEL pipeline linking retriever -> prompt -> LLM
│   │
│   ├── services/
│   │   ├── ingest_service.py    # Ingestion orchestration coordinator
│   │   └── query_service.py     # Query execution coordinator
│   │
│   ├── web/
│   │   ├── server.py            # FastAPI web server and REST routes
│   │   └── static/              # Web assets (index.html, styles.css, app.js)
│   │
│   └── utils/
│       ├── helpers.py           # Helper utilities and timing decorators
│       └── logger.py            # Centralized logging setup
│
├── chroma/                      # ChromaDB SQLite + Parquet vector index
├── data/                        # Raw textbook PDF files (Std 6, 7, 8)
├── tests/                       # Unit and integration test suite
├── requirements.txt             # Pinned project dependencies
└── README.md                    # Quickstart repository documentation
```

---

## ⚡ 6. How to Run the Entire Project

### Step 1: Clone & Setup Virtual Environment
```bash
cd marathi-rag
python -m venv venv
venv\Scripts\activate       # On Windows
# source venv/bin/activate  # On Linux / Mac
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
Create a `.env` file in the root directory:
```env
MISTRAL_API_KEY=your_mistral_api_key_here
MISTRAL_MODEL_NAME=mistral-large-latest
EMBEDDING_MODEL_NAME=BAAI/bge-m3
CHROMA_PERSIST_DIR=chroma
CHUNK_SIZE=400
CHUNK_OVERLAP=80
RETRIEVER_TOP_K=5
```

### Step 3: Ingest the Textbooks (One-time step)
Place textbook PDFs in `data/` and run:
```bash
python -m app.cli.ingest
```

### Step 4: Launch the Web Application
```bash
python -m app.cli.web
```
Open your browser and navigate to **`http://localhost:8000/`**.

---

## 🔮 7. Future Horizons & Next Phases

1. **Audio / Speech Interface**: Voice-in, Voice-out in Marathi so young students can speak directly to the AI tutor without typing.
2. **Automated Quiz & Flashcard Generation**: Teacher tool to generate question banks, fill-in-the-blanks, and grammar quizzes directly from textbook chapters.
3. **Conversational Memory**: Allowing follow-up context in multi-turn dialogues (*"त्यानंतर काय झाले?"*).
4. **Expansion to Standards 9 & 10**: Indexing Kumarbharti textbooks for board exam preparation.
