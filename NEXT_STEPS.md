# 🚀 Marathi RAG Tutor — Quickstart & Resume Guide

All backend code, unit tests, configurations, and pipeline services have been created and verified (**58/58 tests passing**).

When you return to this project, follow this step-by-step checklist.

---

## 📋 Step 1: Environment Setup (.env)

Make sure you are in the `marathi-rag` folder:

```powershell
cd C:\Users\USER\Desktop\NLP\marathi-rag
```

Copy `.env.example` to `.env` if not done already:

```powershell
copy .env.example .env
```

Open `.env` and fill in your keys:

```ini
# --- Required: Mistral AI (For Generating Answers) ---
# Get free key from: https://console.mistral.ai/
MISTRAL_API_KEY=your_mistral_api_key_here

# --- Recommended Option A: Hugging Face API Mode (Zero Download, Fast) ---
# Get free token from: https://huggingface.co/settings/tokens
HF_API_KEY=hf_your_huggingface_token_here
EMBEDDING_MODE=api

# --- Alternative Option B: Local Mode (Downloads 2.27 GB model offline) ---
# If you want offline embeddings without HF token, set:
# EMBEDDING_MODE=local
```

---

## 📥 Step 2: Ingest the Textbook

Make sure your textbook PDF is at `data/textbook.pdf` (it was already copied from `6th.pdf`).

Run the ingestion CLI:

```powershell
python -m app.cli.ingest
```

**What it will do:**
1. Extract 100 pages with PyMuPDF
2. Clean text & normalize Devanagari Unicode
3. Chunk into ~500 semantically aligned chunks
4. Generate embeddings via BAAI/bge-m3
5. Store & persist vectors inside `chroma/` folder

---

## 🌐 Step 3A: Launch the Beautiful Marathi Web UI (Recommended)

To see Marathi text, matras, and conjuncts rendered in high-definition Devanagari font (*Google Fonts Noto Sans Devanagari*), start the web interface:

```powershell
cd C:\Users\USER\Desktop\NLP\marathi-rag
python -m app.cli.web
```

This will automatically open your browser at **`http://127.0.0.1:8000`** with:
- ✨ Clean Marathi Devanagari typography
- 📖 Collapsible textbook page citation drawers
- 💡 1-click sample questions
- 🎓 Rich formatted Marathi answers

---

## 💬 Step 3B: Or Run via Terminal CLI

If querying via terminal, ensure your terminal is set to UTF-8 codepage:

```powershell
cd C:\Users\USER\Desktop\NLP\marathi-rag
chcp 65001
python -m app.cli.query
```

### Sample Questions to Try:
- **Marathi Question:** `या पाठात लेखकाने काय संदेश दिला आहे?`
- **Poem Question:** `कवितेचा भावार्थ काय आहे?`
- **Fact Question:** `आम्ही महाराष्ट्रीयन कन्या या कवितेत कोणाचे वर्णन केले आहे?`
- **Out-of-context Test (To verify grounding refusal):** `भारताचे पंतप्रधान कोण आहेत?`
  *(Should reply: "ही माहिती निवडलेल्या पाठ्यपुस्तकात उपलब्ध नाही.")*

---

## 🧪 Step 4: Run Tests (Whenever you make changes)

```powershell
# Run all fast unit tests
python -m pytest tests/ -v -m "not slow"
```

---

## 📁 Key File Locations

- **Web UI App**: `app/web/server.py` & `app/web/static/`
- **CLI Tools**: `app/cli/web.py`, `app/cli/ingest.py`, `app/cli/query.py`
- **Configuration**: `app/config/settings.py` & `app/config/constants.py`
- **RAG LCEL Chain**: `app/chains/rag_chain.py`
- **System Prompt**: `app/prompts/rag_prompt.py`
- **Vector DB Store**: `chroma/`
- **Application Logs**: `logs/app.log`
