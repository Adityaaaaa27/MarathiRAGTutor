# 📖 Marathi RAG Tutor — Usage & Display Guide

This guide explains how to interact with the Marathi RAG Tutor, including how to use the **Browser Web UI (Recommended)** and how to configure your **Windows Terminal** for clean Devanagari text rendering.

---

## 🌟 Method 1: Interactive Web UI (Recommended)

The Web UI uses **Google Fonts (*Noto Sans Devanagari*)** to render all Marathi text, poetry, complex ligatures, and matras cleanly with modern glassmorphism styling.

### 🚀 How to Launch:
1. Open PowerShell or Command Prompt.
2. Run the following commands:
   ```powershell
   cd C:\Users\USER\Desktop\NLP\marathi-rag
   python -m app.cli.web
   ```
3. Your default web browser will automatically open:
   👉 **`http://127.0.0.1:8000`**

### ✨ Web UI Features:
* **Crystal-Clear Devanagari Typography**: No broken characters or terminal font distortions.
* **Collapsible Textbook Citations**: View the exact source page numbers (e.g., पृष्ठ २७, २८), chapter titles, and excerpts.
* **1-Click Sample Questions**: Instant buttons for poems, stories, and fact-checking.
* **Direct Q&A with Mistral AI**: Grounded exclusively in the Std. 6 Marathi textbook.

---

## 💻 Method 2: Terminal CLI Mode (PowerShell / CMD)

If you prefer to run queries directly inside the terminal, configure Windows console encoding first:

### ⚙️ Step 1: Set Console to UTF-8
In PowerShell or CMD, run:
```powershell
chcp 65001
```

### 🔤 Step 2: Set a Devanagari-Compatible Font
1. Open **Windows Terminal Settings** (`Ctrl + ,`).
2. Under your active profile (e.g., PowerShell), navigate to **Appearance** ➔ **Font face**.
3. Select any Devanagari-supporting font:
   * **`Nirmala UI`** *(Best for Marathi)*
   * **`Mangal`**
   * **`Aparajita`**
   * **`Cascadia Code`** / **`Segoe UI`**

### 💬 Step 3: Run the Query CLI
```powershell
cd C:\Users\USER\Desktop\NLP\marathi-rag
python -m app.cli.query
```

---

## 📥 Ingestion & Maintenance Commands

### Re-Ingesting the Textbook (If PDF changes):
```powershell
cd C:\Users\USER\Desktop\NLP\marathi-rag
python -m app.cli.ingest
```

### Running the Test Suite (58 Unit Tests):
```powershell
cd C:\Users\USER\Desktop\NLP\marathi-rag
python -m pytest tests/ -v -m "not slow"
```

---

## ❓ Sample Questions to Try

| Category | Sample Marathi Question | Expected Behavior |
| :--- | :--- | :--- |
| **Poem Meaning** | `आम्ही महाराष्ट्रीयन कन्या या कवितेत काय सांगितले आहे?` | Explains the poem with page citations (e.g. पृष्ठ २७-२८). |
| **Lesson Summary** | `निसर्गरम्य माथेरान या पाठात माथेरानबद्दल कोणती माहिती दिली आहे?` | Summarizes Matheran's scenic points and travel info. |
| **Letter / Advice** | `आजोबांचे पत्र या पाठात आजोबांनी नातवाला कोणता संदेश दिला आहे?` | Explains grandfather's letter and moral teachings. |
| **Out-of-Book Refusal** | `भारताचे पंतप्रधान कोण आहेत?` | Refusal: *"ही माहिती निवडलेल्या पाठ्यपुस्तकात उपलब्ध नाही."* |

---

## 📁 Key File Locations

- **Web Server & UI**: `app/web/server.py` & `app/web/static/`
- **CLI Commands**: `app/cli/web.py`, `app/cli/query.py`, `app/cli/ingest.py`
- **Vector Database**: `chroma/` (501 chunk embeddings)
- **Configuration**: `app/config/settings.py` & `.env`
- **Application Logs**: `logs/app.log`
