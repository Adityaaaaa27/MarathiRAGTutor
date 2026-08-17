"""
Verify all chapter boundary pages across Stds 6, 7, 8, 9.
Shows first line of each chapter's first page so we can spot misassignments.
"""
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

STANDARDS = {
    6: "data/6th_ocr_cache.json",
    7: "data/7th_ocr_cache.json",
    8: "data/8th_ocr_cache.json",
    9: "data/9th_ocr_cache.json",
}

# Chapter first-page boundaries to check (std -> list of (chapter_first_page, chapter_name))
BOUNDARIES = {
    7: [
        (12, "१. प्रार्थना"),
        (13, "२. श्यामाचे बंधुप्रेम"),
        (18, "३. माझ्या अंगणात"),
        (21, "४. गोपाळाचे शौर्य"),
        (26, "५. दादास पत्र"),
        (29, "६. टप् टप्"),
        (32, "७. आजारी पडण्याचा"),
        (39, "८. शब्दांचे घर"),
        (42, "९. वाचनाचे वेड"),
        (47, "१०. पंडिता रामाबाई"),
        (51, "११. लेख"),
        (55, "१२. रोजनिशी"),
        (58, "१३. अदलाबदल"),
        (63, "१४. संतवाणी"),
    ],
    8: [
        (12, "१. भारत अमुचा देश"),
        (13, "२. चिव चिव चिमण्या"),
        (18, "३. जिकडे तिकडे पाणीच"),
        (20, "४. सावलीतून जा"),
        (25, "५. विश्वविश्वात"),
        (29, "६. कोळ्याची पोर"),
        (32, "७. ध्येयपूर्तीचा"),
        (38, "८. पारखरांचे मागणे"),
        (40, "९. भूमिगत"),
        (46, "१०. जीवन सुंदर करू"),
        (48, "११. प्राणी आणि आपण"),
        (52, "१२. संतवाणी"),
    ],
    9: [
        (12, "१. सर्वात्मका शिवसुंदरा"),
        (14, "२. संतवाणी"),
        (16, "३. बेटा मी एकटो आहे"),  # FIXED
        (22, "४. जि. आय. पी. रेल्वे"),
        (26, "५. रंग माझा वेगळा"),
        (29, "६. त्याचे जगणे"),
        (33, "७. मनाचे श्लोक"),
        (36, "८. कुसुमाग्रज"),
        (41, "९. आभाळातल्या पाऊलवाटा"),
        (46, "१०. वीणा"),
        (49, "११. वसुधैव कुटुंबकम"),
        (53, "१२. वाट पाहताना"),
        (55, "१३. दिव्याची ज्योत"),
        (60, "१४. ते जीवनदायी झाड"),
        (64, "१५. माझे शिक्षक व संस्कार"),
    ],
}

for std, boundaries in BOUNDARIES.items():
    cache_path = STANDARDS[std]
    if not Path(cache_path).exists():
        print(f"Std {std}: cache not found")
        continue
    
    d = json.load(open(cache_path, encoding='utf-8'))
    print(f"\n{'='*65}")
    print(f"STANDARD {std} — Chapter Boundary Verification")
    print('='*65)
    
    for page_num, chapter_hint in boundaries:
        text = d.get(str(page_num), "")
        first_line = text[:120].replace('\n', ' ')
        print(f"  P{page_num:02d} [{chapter_hint[:25]:25s}]: {first_line}")
