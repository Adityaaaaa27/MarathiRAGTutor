# Multi-Standard Marathi Textbook RAG System: Diagnosis, Fixes & Verification Guide

## 📌 Executive Summary

This document provides a comprehensive technical overview of the issues diagnosed across the Maharashtra State Board Marathi textbooks (Standards 6th, 7th, 8th, 9th), the architectural fixes implemented to ensure **100% strict standard-level isolation**, and the verification test results.

---

## 🔍 1. Root Cause Analysis (Why Standards 7, 8, 9 Failed Initially)

During vector store inspection and OCR text cache analysis, four primary issues were identified:

| Issue | Root Cause | Impact |
| :--- | :--- | :--- |
| **1. Std 9 Cross-Standard Bleed-Through** | The regex pattern `r"^([०-९\d]+)\.\s*([^\n]+)"` in `chunker.py` matched exercise question numbers inside Std 9 pages (e.g., `६. ...`) and mistakenly mapped them to **Std 6 chapter names** (*"अमुचा बाग"*, *"आम्ही महाराष्ट्रकन्या"*). | Std 9 content was tagged with Std 6 chapter names, breaking retrieval relevance. |
| **2. Std 7 & 8 Generic Chapter Metadata** | Many pages in Std 7 and Std 8 lacked top-level heading formats matching regexes, causing 24+ chunks in each textbook to be assigned the fallback chapter name `"प्रस्तावना"` (Introduction). | Chapter-targeted retrieval could not locate key chapters like *"श्यामाचे बंधुप्रेम"* or *"स्टीफन हॉकिंग"*. |
| **3. Std 10 OCR Contamination** | 48 out of 204 pages in `10th.pdf` contained English OCR response artifacts (`[BLANK PAGE - Note: English image]`). | Corrupted vector search results. *(Std 10 was completely purged per user instruction)*. |
| **4. `CHAPTER_KEYWORDS` Coverage Gap** | `app/chains/rag_chain.py` only contained chapter detection keywords for Std 6. | Queries targeting Std 7, 8, or 9 chapters never triggered chapter-level retrieval routing. |
| **5. Multi-field ChromaDB Filter Syntax** | ChromaDB threw an error when combining `standard` and `chapter` in dictionary syntax without an explicit `$and` operator: `Expected where to have exactly one operator`. | Multi-condition filtering crashed during query execution. |

---

## 🛠️ 2. Solutions Implemented

### A. Per-Standard Page-to-Chapter Maps
In `app/preprocessing/chunker.py`, exact page mappings were created for all active standards:

- **Standard 6 (100 pages):** `PAGE_CHAPTER_MAP_6` (*"या भारतात बंधुभाव"*, *"चिमणीचं घरटं"*, *"निसर्गरम्य माथेरान"*, etc.)
- **Standard 7 (66 pages):** `PAGE_CHAPTER_MAP_7` (*"प्रार्थना"*, *"श्यामाचे बंधुप्रेम"*, *"गोपाळाचे शौर्य"*, *"दादास पत्र"*, *"आजारी पडण्याचा प्रयोग"*, *"पंडिता रामाबाई"*, *"अदलाबदल"*, etc.)
- **Standard 8 (58 pages):** `PAGE_CHAPTER_MAP_8` (*"भारत अमुचा देश"*, *"चिव चिव चिमण्या"*, *"सावलीतून जा"*, *"स्टीफन हॉकिंग"*, *"ध्येयपूर्तीचा ध्यास"*, *"भूमिगत"*, etc.)
- **Standard 9 (92 pages):** `PAGE_CHAPTER_MAP_9` (*"सर्वात्मका शिवसुंदरा"*, *"संतवाणी"*, *"बेटा मी एकटो आहे"*, *"जि. आय. पी. रेल्वे"*, *"कुसुमाग्रज"*, *"दिव्याची ज्योत"*, *"माझे शिक्षक व संस्कार"*, etc.)

### B. Multi-Standard Chapter Detection Routing
In `app/chains/rag_chain.py`, `CHAPTER_KEYWORDS` was expanded to include chapter names, author names, and key terms across all 4 standards.

### C. ChromaDB Multi-Key `$and` Filter Normalization
In `app/vectorstore/chroma_service.py`, filter dictionaries with multiple keys are automatically wrapped inside `$and`:
```python
if len(cleaned_filters) > 1:
    kwargs["filter"] = {"$and": [{k: v} for k, v in cleaned_filters.items()]}
elif len(cleaned_filters) == 1:
    kwargs["filter"] = cleaned_filters
```

### D. Clean Re-Ingestion & Purging
Re-ingested Standards 7, 8, 9 using cached OCR data and the new chapter maps. Purged all Std 10 documents.

---

## 📊 3. Database Chunk Statistics

| Standard | Textbook Name | Pages | Chunks in Vector DB | Status |
| :---: | :--- | :---: | :---: | :---: |
| **Std 6** | बालभारती (इयत्ता सहावी) | 100 | **255** | ✅ Active & Verified |
| **Std 7** | बालभारती / सुलभभारती (इयत्ता सातवी) | 66 | **166** | ✅ Active & Verified |
| **Std 8** | बालभारती / सुगमभारती (इयत्ता आठवी) | 58 | **141** | ✅ Active & Verified |
| **Std 9** | अक्षरभारती / कुमारभारती (इयत्ता नववी) | 92 | **290** | ✅ Active & Verified |
| **Std 10** | — | — | **0** | ⛔ Excluded (Purged) |
| **Total** | **Unified Collection (`marathi_textbooks_all`)** | **316** | **852** | ✅ Cleanly Indexed |

---

## 🧪 4. Verification & Standard Isolation Test Results

### Test Case 1: Standard 6
- **Query:** `चिमणीचं घरटं या पाठात चिमणीने आपले घरटे कुठे बांधले होते?`
- **Selected Standard:** `6`
- **Retrieved Chunks:** 10 chunks from Pages [12, 13, 14, 15, 16]
- **Standard Isolation:** ✅ **100% Std 6**
- **Answer:** Grounded summary explaining the sparrow's nest and Isha's conversation in Std 6.

### Test Case 2: Standard 7
- **Query:** `श्यामाचे बंधुप्रेम या पाठात श्यामने आपल्या भावासाठी काय आणले होते आणि लेखक कोण आहेत?`
- **Selected Standard:** `7`
- **Retrieved Chunks:** 10 chunks from Pages [13, 14, 16, 17]
- **Standard Isolation:** ✅ **100% Std 7**
- **Answer:** *"श्यामने आपल्या लहान भावासाठी नवीन कोट आणला होता. या पाठाचे लेखक साने गुरुजी (पांडुरंग सदाशिव साने) आहेत."*

### Test Case 3: Standard 8
- **Query:** `स्टीफन हॉकिंग कोणत्या विषयाचे शास्त्रज्ञ होते?`
- **Selected Standard:** `8`
- **Retrieved Chunks:** 7 chunks from Pages [25, 26, 27]
- **Standard Isolation:** ✅ **100% Std 8**
- **Answer:** *"स्टीफन हॉकिंग हे भौतिकशास्त्र या विषयाचे शास्त्रज्ञ होते. त्यांनी विश्वाच्या निर्मिती आणि कृष्णविवरांबद्दल महत्त्वाचे संशोधन केले."*

### Test Case 4: Standard 9
- **Query:** `जि. आय. पी. रेल्वे या पाठाचे लेखक कोण आहेत आणि रेल्वे कधी सुरू झाली?`
- **Selected Standard:** `9`
- **Retrieved Chunks:** 10 chunks from Pages [22, 23, 24, 25]
- **Standard Isolation:** ✅ **100% Std 9**
- **Answer:** *"या पाठाचे लेखक प्रबोधनकार ठाकरे (केशव सीताराम ठाकरे) आहेत. भारतातील पहिली रेल्वे १६ एप्रिल १८५३ रोजी मुंबईहून ठाण्याला सुरू झाली."*

### Test Case 5: Cross-Standard Isolation & Refusal Test
- **Query:** `स्टीफन हॉकिंग यांच्याबद्दल काय माहिती दिली आहे?` *(Std 8 Topic)*
- **Selected Standard:** `7` *(Std 7 selected)*
- **Result:**
  - `where={"$and": [{"standard": 7}, {"chapter": "५. विश्वविश्वात शास्त्रज्ञ - स्टीफन हॉकिंग"}]}` returned **0 results** (Chapter exists only in Std 8).
  - General search in Std 7 found no Stephen Hawking mentions.
- **Answer:**
  > **"ही माहिती निवडलेल्या पाठ्यपुस्तकात उपलब्ध नाही."** *(Strict grounding refusal, zero data leak from Std 8)*

---

## 🚀 5. How to Run & Use the System

### Running the Web Interface
```powershell
python -m app.web.server
```
Open **`http://localhost:8000`** in your browser. Use the pill bar or dropdown to select your standard (6th, 7th, 8th, 9th, or All Standards).

### Running Isolation & Accuracy Tests
```powershell
python -m scratch.test_standard_isolation
```
