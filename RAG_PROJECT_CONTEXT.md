# 📚 Marathi RAG Tutor - Project Context & Execution Guide

This document preserves the complete context of the Marathi RAG pipeline fixes, dataset details, and instructions for execution.

---

## 🔍 1. Textbook Structure (100-Page Edition)

The textbook in `data/textbook.pdf` is the **100-page edition** of the Maharashtra State Board Standard 6 Marathi textbook (*शिकू मराठी आनंदाने*).

### **Complete Official Table of Contents (अनुक्रमणिका)**
*   **Part 1 (भाग - १):**
    1. **१. या भारतात बंधुभाव (प्रार्थना)** – *राष्ट्रसंत श्री तुकडोजी महाराज* (पृष्ठ १)
    2. **२. चिमणीचं घरटं** – *अलका उमरणीकर* (पृष्ठ २)
    3. **३. जिकडे तिकडे पाणीच पाणी (कविता)** – *शंकर वैद्य* (पृष्ठ ७)
    4. *चित्रवाचन* (पृष्ठ १०)
    5. **४. आम्ही महाराष्ट्रकन्या (कविता)** – *पद्मा गोळे* (पृष्ठ १२)
    6. **५. आईचे पत्र** (पृष्ठ १६)
*   **Part 2 (भाग - २):**
    7. **६. अमुचा बाग विकसनशील छान (कविता)** – *यशवंत देव* (पृष्ठ २१)
    8. **७. आजोबांचा तीन पुड्यांचा डबा** – *अदिती देवधर* (पृष्ठ २५)
    9. **८. नव्या युगाची गाणी (कविता)** – *वंदना विटणकर* (पृष्ठ ३२)
    10. **९. निसर्गरम्य माथेरान** – *सुशील दुधाणे* (पृष्ठ ३५)
    11. *अनुभव लेखन* (पृष्ठ ३८)
*   **Part 3 (भाग - ३):**
    12. *बातमी आकलन* (पृष्ठ ४०)
    13. **१०. मी मोठा की लहान?** – *सुनंदा उमर्जी* (पृष्ठ ४२)
    14. **११. गवतफुला रे! गवतफुला! (कविता)** – *इंदिरा संत* (पृष्ठ ४६)
    15. **१२. जाहिरात** (पृष्ठ ५०)
    16. **१३. गणितातील एक कूटप्रश्न** – *दिवाकर बापट* (पृष्ठ ५५)
    17. **१४. सुगी (कविता)** – *संतोष आळंजरकर* (पृष्ठ ६०)
*   **Part 4 (भाग - ४):**
    18. **१५. थोरांची ओळख:**
        - *(अ) डॉ. ए. पी. जे. अब्दुल कलाम* (पृष्ठ ६४)
        - *(आ) लालबहादूर शास्त्री* – *जयसिंगराव राठोड* (पृष्ठ ६५)
    19. **१६. मायबोली (कविता)** – *सुरेश भट* (पृष्ठ ६६)
    20. **१७. आपली संस्कृती, आपल्या परंपरा** (पृष्ठ ७१)
    21. **१८. नव्या तू (कविता)** – *राजेंद्र आरेकर* (पृष्ठ ७७)
    22. **१९. विभूतींची भंबेरी** – *प्र. के. अत्रे* (पृष्ठ ८१)
    23. *माझा अनुभव (अनुभव लेखन)* (पृष्ठ ८७)
    24. **२०. विचारधन** (पृष्ठ ८८)

---

## 🛠️ 2. Core Fixes Applied to the RAG Pipeline

1. **Legacy Font Decoder (`cleaner.py`):**
   - The PDF uses legacy *Shree-Dev* / *BalBharati* non-Unicode font encodings that caused text extractors to output corrupted Devanagari characters (e.g. `विनासागथरम्1 माार्थेराना` instead of `निसर्गरम्य माथेरान`, `विचांमाणी` for `चिमणी`, etc.).
   - Added `_decode_legacy_fonts` in `cleaner.py` to systematically decode these ligatures and normalize words into standard Unicode Devanagari.

2. **Context-Enriched Chunks & Page Mapping (`chunker.py`):**
   - Mapped all 100 pages via `PAGE_CHAPTER_MAP` and prepended contextual headers `[<chapter_name> | पृष्ठ: <page_number>]` to every chunk. This ensures strong semantic matching and prevents cross-chapter confusion.

3. **Accurate Synthetic Table of Contents (`ingest_service.py`):**
   - Integrated full 20-chapter TOC chunks mapped to Page 10 so high-level syllabus queries receive complete, structured answers.

4. **Retriever & Chunk Size Optimization (`settings.py`, `.env`):**
   - `chunk_size = 800`, `chunk_overlap = 150`, `retriever_top_k = 10`.

---

## 🚀 3. How to Run and Interact

### **Option A: Web UI (Browser)**
```powershell
cd C:\Users\USER\Desktop\NLP\marathi-rag
python -m app.cli.web
```
Open **http://127.0.0.1:8000** in your browser.

### **Option B: Terminal Interactive Mode**
```powershell
cd C:\Users\USER\Desktop\NLP\marathi-rag
chcp 65001
python -m app.cli.query
```

### **Option C: Re-ingest Dataset**
```powershell
cd C:\Users\USER\Desktop\NLP\marathi-rag
python -m app.cli.ingest
```

---

## 🧪 4. Verified Questions & Output Accuracy

- **Q: या पाठ्यपुस्तकात कोणकोणते पाठ आणि कविता आहेत?**  
  👉 Returns the complete structured 20-chapter syllabus from Parts 1 to 4 with author names and page numbers.
- **Q: निसर्गरम्य माथेरान या पाठात माथेरानबद्दल कोणती माहिती दिली आहे?**  
  👉 Returns accurate geographic, transportation (Neral toy train, vehicle ban), and trekking details citing pages 45–49.
- **Q: चिमणीचं घरटं या पाठात काय सांगितले आहे?**  
  👉 Returns accurate narrative of Isha, her mother, artificial nests, and bird conservation citing pages 12–15.
- **Q: आजोबांचा तीन पुड्यांचा डबा या पाठातून काय संदेश मिळतो?**  
  👉 Returns grandfather's 40-year steel box lesson on stopping plastic usage citing pages 35–38.
- **Q: सोलर सिस्टीममध्ये किती ग्रह आहेत?**  
  👉 Correctly refuses out-of-syllabus query with `"ही माहिती निवडलेल्या पाठ्यपुस्तकात उपलब्ध नाही."`.
