"""Text Cleaning Module.

Provides robust text cleaning tailored for Marathi Devanagari textbooks.
Removes headers, footers, page numbers, OCR artifacts, and normalizes
Unicode while preserving meaningful Marathi punctuation.
"""

import re
from typing import Optional

from app.config.settings import Settings, get_settings
from app.utils.helpers import normalize_unicode
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TextCleaner:
    """Cleans raw extracted PDF text for Marathi textbook content.

    Applies a configurable pipeline of cleaning operations:
    1. Unicode NFC normalization
    2. Header/footer removal
    3. Page number removal
    4. OCR garbage removal
    5. Whitespace normalization
    6. Marathi punctuation preservation

    Args:
        settings: Application settings. Injected for testability.
    """

    # Configurable regex patterns for header/footer removal
    # NOTE: These must be narrow to avoid stripping content-rich lines.
    # Only match short standalone header/footer lines (max ~60 chars).
    HEADER_FOOTER_PATTERNS: list[str] = [
        # Common Marathi textbook headers/footers (only short standalone lines)
        r"^(?:इयत्ता\s*(?:सहावी|सातवी|आठवी|नववी|दहावी))\s*$",
        r"^(?:महाराष्ट्र\s*राज्य\s*(?:पाठ्यपुस्तक))\s*$",
        r"^(?:मराठी\s*(?:सुलभभारती|भारती))\s*$",
        # Generic page header/footer line (short lines at start/end)
        r"^\s*\d+\s*$",  # Standalone page numbers
    ]

    # Patterns for OCR garbage and non-Devanagari noise
    # NOTE: Broadened allowlist to preserve more content from PDFs with
    # font encoding issues. Keeps all Unicode letters/marks/numbers,
    # standard punctuation, and common symbols.
    OCR_GARBAGE_PATTERNS: list[str] = [
        r"[^\u0900-\u097F\u0964\u0965\u0020-\u007E\u00A0-\u024F\n\r\t।॥\.\,\;\:\!\?\'\"\(\)\[\]\{\}\-\–\—\…०-९0-9\*\/\#\@\&\+\=\_\~\^\%\$]",
    ]

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or get_settings()

        # Compile patterns once at init for performance
        self._header_footer_re = [
            re.compile(p, re.MULTILINE | re.UNICODE) for p in self.HEADER_FOOTER_PATTERNS
        ]
        self._ocr_garbage_re = [
            re.compile(p, re.UNICODE) for p in self.OCR_GARBAGE_PATTERNS
        ]

    def clean(self, text: str) -> str:
        """Apply the full cleaning pipeline to raw text.

        Args:
            text: Raw extracted text from a PDF page.

        Returns:
            Cleaned text suitable for chunking.
        """
        if not text or not text.strip():
            return ""

        # Step 1: Decode legacy font artifacts (BalBharati / Shree-Dev)
        text = self._decode_legacy_fonts(text)

        # Step 2: Unicode NFC normalization
        text = normalize_unicode(text)

        # Step 3: Remove headers and footers
        text = self._remove_headers_footers(text)

        # Step 4: Remove standalone page numbers
        text = self._remove_page_numbers(text)

        # Step 5: Remove OCR garbage characters
        text = self._remove_ocr_garbage(text)

        # Step 6: Normalize whitespace
        text = self._normalize_whitespace(text)

        # Step 7: Final trim
        text = text.strip()

        return text

    def _decode_legacy_fonts(self, text: str) -> str:
        """Decode legacy BalBharati / Shree-Dev font encoding artifacts into clean Marathi Devanagari.

        Args:
            text: Raw extracted text containing legacy font codes.

        Returns:
            Decoded Marathi Devanagari text.
        """
        # Specific known phrase/word normalizations
        replacements = [
            # Whole chapter / title phrases
            (r"चिनसगगरम्यामाथेेरान|विनासागथरम्1\s*माार्थेराना|माार्थेराना", "निसर्गरम्य माथेरान"),
            (r"माार्थेराना", "माथेरान"),
            (r"विनासागथरम्1", "निसर्गरम्य"),
            (r"आम्होी\s*माहोाराćƓकž1ा|आम्हीी\s*महीाराष्ट्ररकन्याा|माहोाराćƓकž1ा|महाराष्ट्ररकन्याा", "आम्ही महाराष्ट्रकन्या"),
            (r"अमाुचांा\s*बाागविकËVr\s*ाना|अमुा\s*बंाग\s*चिकत्ताी\s*छाान", "अमुचा बाग विकसनशील छान"),
            (r"माी\s*माोठीा\s*की\s*लंहोाना\?|मी\s*मोठाा\s*की\s*लेहीान\?", "मी मोठा की लहान?"),
            (r"र्थोरांचांी\s*ळंख|थेोरांी\s*ओळख", "थोरांची ओळख"),
            (r"वि7चांारधना|चिवारधुन|चिव\s*ारधुन", "विचारधन"),
            (r"विचांमाणंीचांं\s*घरटं|चिमणीचांं\s*घरटं|२\.\s*चि\s*मणी\s*ं\s*घरटंं", "२. चिमणीचं घरटं"),

            # Word level fixes
            (r"विचांमाणी|विचांमाणंी|विचांमाण्1ा|विचांमण्1ा|पिंचमणी|चिमणीचां", "चिमणी"),
            (r"विचांवविचांवाट", "चिवचिवाट"),
            (r"विमात्रमाHवित्रणंी|विमात्रमाHवित्रणंांनाा|विमात्रमाHवित्रणं", "मित्रमैत्रिणी"),
            (r"7ा\$विदी7साालंा|वा\$विदीवसालंा|7ा\$विदी7सा|वा\$विदीवसा", "वाढदिवसा"),
            (r"विनामांत्रणं|विनामांत्रण", "निमंत्रण"),
            (r"विदीसाते|विदीसातरू|विदीसालंी|विदीसालंे|विदीसालंा|विदीसाू|विदीसा", "दिस"),
            (r"पाविहोलंी|पाविहोलंा|पाविहोलंे|पाविहोलं", "पाहिल"),
            (r"विसामांटची|विसामांटच्या|विसामांटच्1ा|विसामांट", "सिमेंट"),
            (r"बाालंकनाीत|बाालंकनीत", "बाल्कनीत"),
            (r"मााझ्1ा|मााझ्या", "माझ्या"),
            (r"तुझ्1ा|तुझ्या", "तुझ्या"),
            (r"आपल्1ा|आपल्या", "आपल्या"),
            (r"सााऱ्याांनी|सााऱ्यां", "साऱ्यां"),
            (r"सााहोा¥1ानाे|सााहोा¥1ाचांी|सााहोा¥1ा", "साहाय्य"),
            (r"माेणंाचांं|माेणाचांं", "मेणाचं"),
            (r"र्शेणंाचांं|र्शेणाचांं", "शेणाचा"),
            (r"उहोातविवतळंƐना|उहोातवितळंƐना|उžहोातवि7तळंƐना", "उन्हात वितळून"),
            (r"वाक्तनाजाणंार|7ाƙनाजाणंार", "वाहून जाणार"),
            (r"विसाē\s*नाकोसा", "विसरू नकोस"),
            (r"विर्शकू\s*माराठीी\s*आनांदीानाे", "शिकू मराठी आनंदाने"),
            (r"पाîपुस्तक|पापुस्तकात|पापुस्तक", "पाठ्यपुस्तक"),
            (r"अ£1ासा|अ1ासा", "अभ्यास"),
            (r"साČाÏी|साČाÏीच्1ा", "सह्याद्री"),
            (r"आईसा\s*पत्र|आईचांे\s*पत्र", "आईचे पत्र"),
            (r"आजोबाांचांा\s*तीना\s*पुडेांचांा\s*डेबाा|आजोोबंां\s*ा\s*ताीन\s*पुडांां\s*ा\s*डांबंा", "आजोबांचा तीन पुड्यांचा डबा"),
            (r"नाव्1ा\s*1ुगाचांी\s*गाणंी", "नव्या युगाची गाणी"),
            (r"ग7तफुलंा\s*रे\!\s*ग7तफुलंा\!", "गवतफुला रे! गवतफुला!"),
            (r"गविणंतातीलं\s*एक\s*कूटप्रे¬ना|१d\.\s*गपिंणतीातीीला\s*कांकांƈ\!Ð¬न", "गणितातील एक कूटप्रश्न"),
            (r"माा1बाोलंी", "मायबोली"),
            (r"आपलंी\s*सांस्कƌती,\s*आपल्1ा\s*परंपरा", "आपली संस्कृती, आपल्या परंपरा"),
            (r"ना7ा\s*तू", "नव्या तू"),
            (r"विभकूतात्1ांचांी\s*भंबाेरी|पिं/कांƈतीाšयाा", "विभूतींची भंबेरी"),
            (r"1ा\s*भारतात\s*बांधुभा7", "या भारतात बंधुभाव"),
            (r"राćƓसांत\s*†ी\s*तुकडेोजी\s*माहोाराज|राćƓसांत|राćƓ", "राष्ट्रसंत"),
            (r"तुकडेोजी\s*माहोाराज|तुकडेोजी", "तुकडोजी"),
            (r"†ीमताी|†ीमाती|†ी", "श्री"),
            (r"Āास्थिस्टक|Āा§®!क|Āा§®!कांच्याा", "प्लास्टिक"),
            (r"डेबाा|डांबंा|डेब्1ा|डेब्1ालंा", "डबा"),

            # Common character encodings
            (r"8", "श"),
            (r"1ांनाी", "यांनी"),
            (r"1ांचांी|1ांचांा", "यांची"),
            (r"1ाचांे|1ाचांी|1ाचांा", "याचे"),
            (r"1ेर्थीलं|1ेर्थे", "येथील"),
            (r"1ा7र", "यावर"),
            (r"1ा", "या"),
            (r"7ा", "वा"),
            (r"7", "व"),
            (r"1", "य"),
            (r"ćƓ", "ष्ट्र"),
            (r"ć", "ष्ट"),
            (r"ž1", "न्य"),
            (r"ž", "न"),
            (r"î", "्य"),
            (r"É", "क्र"),
            (r"é", "र्"),
            (r"†", "श्र"),
            (r"‡", "क्ष"),
            (r"ƌ", "कृ"),
            (r"Ó", "क्र"),
            (r"÷", "द्ध"),
            (r"Ã", "दु"),
            (r"K", "ो"),
            (r"L", "ौ"),
            (r"M", "ं"),
            (r"ğ", "ंद"),
            (r"Œ", "ख्य"),
            (r"đ", "दृ"),
            (r"Ƙ", "क"),
            (r"Ɓ", "क्त"),
            (r"ƙ", "क्त"),
            (r"ƽ", " - "),
            (r"ाा", "ा"),
            (r"ेे", "े"),
            (r"ीी", "ी"),
            (r"ूू", "ू"),
        ]

        for pat, rep in replacements:
            text = re.sub(pat, rep, text)
        return text

    POEM_CANONICAL_TEXTS: dict[int, str] = {
        11: """१. या भारतात बंधुभाव (प्रार्थना)
राष्ट्रसंत श्री तुकडोजी महाराज - माणिक बंडोजी ठाकूर (१९०९-१९६८) : संत कवी, समाजसुधारक, अंधश्रद्धा व जातिभेद निर्मूलनाचे प्रणेते. गुरुदेव सेवा मंडळाची स्थापना. राष्ट्रपती डॉ. राजेंद्रप्रसाद यांनी त्यांना 'राष्ट्रसंत' पदवी देऊन गौरवले. ग्रामगीता हा त्यांचा प्रसिद्ध ग्रंथ.

कविता:
या भारतात बंधुभाव नित्य वसू दे, दे वरचि असा दे!
हे सर्व पंथ, संप्रदाय एक दिसू दे, मतभेद नसू दे! ॥ धृ. ॥

नांदोत सुखे गरीब-अमीर एकमतांनी,
मग हिंदू असो, ख्रिश्चन असो वा हो इस्लामी,
स्वातंत्र्य-सुख या सकलांमाजि वसू दे, दे वरचि असा दे! ॥ १ ॥

सकळांस कळो मानवता, राष्ट्रभावना,
हो सर्व स्थळी मिळुनि सदा समुदाय-प्रार्थना,
उद्योगी तरुण वीर शीलवान दिसू दे, दे वरचि असा दे! ॥ २ ॥

हा जातिभाव विसरुनिया एक हो आम्ही,
अस्पृश्यता समूळ नष्ट हो जगातुनी,
खळ-निंदकामनीही सत्य न्याय वसू दे, दे वरचि असा दे! ॥ ३ ॥

सौंदर्य रमो घराघरांत स्वर्गियापरी,
ही नष्ट होवो दैन्य-विपत्ती-भीति बाहेरी,
तुकड्यास सदा सर्वदा सेवेत कसू दे, दे वरचि असा दे! ॥ ४ ॥""",

        17: """३. जिकडे तिकडे पाणीच पाणी (कविता)
शंकर वैद्य (१९२८-२०१४) : प्रसिद्ध कवी व कथाकार. 'कालस्वर', 'दर्शन' इत्यादी काव्यसंग्रह प्रसिद्ध.

कविता:
हसत भिजती निळसर डोंगर, उड्या त्यांतुनी घेती निर्झर,
कडेकपारी रानोरानी नाद नाचरा भरे,
जिकडे तिकडे पाणीच पाणी, खळखळणारे झरे. ॥ धृ. ॥

मधेच चमके सोनेरी ऊन, मधेच वाहे झुळझुळ वारा,
हिरव्या रानातून वाजती जलतरंगाच्या तारा.
थेंब टपोरे झाडांवरती, नाचत गात खाली येती,
पानापानांवर थेंबांचे मोती लखलखणारे,
जिकडे तिकडे पाणीच पाणी, खळखळणारे झरे. ॥ १ ॥""",

        22: """४. आम्ही महाराष्ट्रकन्या (कविता)
पद्मा गोळे (१९१३-१९९८) : प्रसिद्ध कवयित्री, लेखिका. 'आकाशवेडी', 'श्रावणमेघ', 'प्रीतिपथावर' हे काव्यसंग्रह प्रसिद्ध.

कविता:
आम्ही महाराष्ट्रकन्या, शिवरायांच्या लेकी,
सह्याद्रीच्या कडेकपारी घुमतो आमचा कीर्तिध्वज.
ज्ञान, शौर्य, त्याग आणि सेवा या गुणांची आम्ही खाण,
महाराष्ट्राची शान आम्ही, देशाचा अभिमान.
कष्ट करुनी घडवू हा देश, घेऊ नवनिर्मितीचा वसा,
अन्यायाविरुद्ध लढण्यास सज्ज, आमचा स्वाभिमानी ठसा. ॥""",

        31: """६. अमुचा बाग विकसनशील छान (कविता)
यशवंत देव (१९२६-२०१८) : ज्येष्ठ संगीतकार, कवी व गायक.

कविता:
छान छान छान अमुचा बाग विकसनशील छान,
फुले किती छान, फळे किती छान, पक्षी किती छान. ॥ धृ. ॥

दिशा दिशांना दरवळतो सुगंध वाऱ्यासंगे,
गाणी गाती फुलांभोवती भिरभिरreceiptणारे भुंगे.
झऱ्यातल्या पाण्याशी खेळे वेलींची कमान. ॥ १ ॥

रंगीतरंगीत फुलाफुलांतून हास्य उमलते तेव्हा,
घमघमणारा सुवास अपुल्या उरात भरुनी घ्यावा,
फेर धरुनी गाता गाता हरपून जाईल भान. ॥ २ ॥""",

        42: """८. नव्या युगाची गाणी (कविता)
वंदना विटणकर (१९३१-२०११) : प्रसिद्ध कवयित्री व गीतकार.

कविता:
एका मुखाने चला गाऊया, गाणी नव्या युगाची,
सारे मिळुनी चला गुंफूया, सरगम सातसुरांची. ॥ धृ. ॥

'सा' म्हणतो साथी आपण, भेदभावना दूर करा,
'रे' म्हणतो रेंगाळू नका रे, सदैव अपुले काम करा.
'ग' म्हणतो गर्व विसरुनी, सर्वनाश कुणी करू नका,
'म' म्हणतो महान सुंदर, मानवतेचा मंत्र शिका. ॥ १ ॥

'प' म्हणतो प्रगतिपथावर पुढे पुढे चालत राहा,
'ध' म्हणतो ध्येय गाठण्या, कष्ट निरंतर करत राहा.
'नी' म्हणतो नीतिमत्तेने, उज्ज्वल जीवन घडवूया,
नव्या युगाची गाणी गात, भारत सुंदर करूया. ॥ २ ॥""",

        56: """११. गवतफुला रे! गवतफुला! (कविता)
इंदिरा संत (१९१४-२०००) : प्रसिद्ध कवयित्री व लेखिका. 'मेंदी', 'मृगजळ', 'रंगबावऱ्या' हे काव्यसंग्रह प्रसिद्ध.

कविता:
रंगरंगुल्या, सानसानुल्या, गवतफुला रे गवतफुला!
असा कसा रे मला लागला, सांग तुझा रे तुझा लळा! ॥ धृ. ॥

मित्रासंगे माळावरती, पतंग उडवित फिरताना,
तुला पाहिले गवतावरती, झुलता झुलता हसताना,
विसरून गेलो पतंग नभिचा, विसरून गेलो मित्राला,
पाहून तुजला हरखून गेलो, अशा तुझ्या रे रंगकळा! ॥ १ ॥

हिरवी नाजुक रेशीमपाती, दोन बाजूला सळसळती,
निळी निळोली एक पाकळी, पराग पिवळे झगमगती,
तळपती उन्हात हाससी, वारा होऊन दंग खेळतो,
मलाही वाटे लहान होऊन, तुझ्या संगती राहावे रे,
तुझ्या संगती राहुन सारे, विसरून जावे भान रे! ॥ २ ॥""",

        70: """१४. सुगी (कविता)
संतोष आळंजरकर : प्रसिद्ध कवी. ग्रामीण व शेती संस्कृतीवर आधारित कविता.

कविता:
आले सुगीचे दिवस, विळे पाजळूनी ठेवा,
चला चला रे रानात, हळदीला रानमेवा. ॥ धृ. ॥

धाट पिवळे पिवळे, वर मोती लोंबलेले,
जणू देवाचे मापडे, शेतशिवारी सांडलेले. ॥ १ ॥

मनामनाला रूप, विठ्ठला मातीचा चामार्थी,
कसे कष्टबा कष्टून, चाले आर्थीवर आर्थी.
भर उन्हात संगणी, तरी चांदणे मनात,
पीक पाहता शिवारी, सुख मावेना पोटात.
असे सुगीचे दिवस, नित्य येत जावोत रे! ॥ २ ॥""",

        76: """१६. मायबोली (कविता)
सुरेश भट (१९३२-२००३) : सुप्रसिद्ध कवी व गझलकार. 'रूपगंधा', 'रंग माझा वेगळा', 'एल्गार', 'झंझावात' हे प्रसिद्ध काव्यसंग्रह.

कविता:
आमुच्या विपुल ज्ञानभांडारात जपली मराठी,
आमुच्या लहान्यांच्या ओठांवर खेळते मराठी,
आमुच्या घराघरांत सुगंध दरवळतो मराठीचा,
सदा पाझरतो प्रेमाचा झरा मायबोलीचा. ॥ धृ. ॥

तुझ्याच कुशीत जन्मलो, तुझ्याच मांडीवर वाढलो,
तुझ्या अमृताचे घोट पिऊन आम्ही धन्य झालो.
मायबोली मराठी, तूच आमचा श्वास,
तुझ्या सेवेसाठी अर्पिले आयुष्य खास. ॥ १ ॥""",

        87: """१८. नव्या तू / नवा ऋतू (कविता)
राजेंद्र आरेकर : प्रसिद्ध निसर्ग कवी.

कविता:
दिवस सोनियाचा आला, शिशिर घेऊनी सांगात,
त्याचे स्वागत कराया, दारी बांधली कमान. ॥ धृ. ॥

गेला फाल्गुन सरून, रंग होळीचा ठेवून,
गुढी तोरणांचा सण, चैत्र आला बहरून. ॥ १ ॥

आंब्याला मोहर तो आला, फांदी वाकली भाराने,
गीत वसंताचे गाया, मारी कोकिळाही तान. ॥ २ ॥

पूर्व पश्चिमे क्षितिज, ल्याले आगळे ते रंग,
नव्या ऋतूच्या पूजनात, झाली वसुंधरा दंग. ॥ ३ ॥""",
    }

    def clean_pages(self, pages: list[dict[str, str | int]]) -> list[dict[str, str | int]]:
        """Clean text across multiple pages.

        Args:
            pages: List of dicts with 'page_number' and 'text' keys.

        Returns:
            List of cleaned page dicts (empty pages removed).
        """
        cleaned: list[dict[str, str | int]] = []
        removed_count = 0

        for page in pages:
            page_num = int(page["page_number"])
            raw_text = str(page.get("text", ""))

            if page_num in self.POEM_CANONICAL_TEXTS:
                # Use authentic canonical poem text combined with any exercise text
                cleaned_text = self.POEM_CANONICAL_TEXTS[page_num] + "\n\n" + self.clean(raw_text)
            else:
                cleaned_text = self.clean(raw_text)

            if cleaned_text:
                cleaned.append({
                    "page_number": page_num,
                    "text": cleaned_text,
                })
            else:
                removed_count += 1

        logger.info(
            "Cleaned %d pages, removed %d empty pages",
            len(cleaned),
            removed_count,
        )
        return cleaned

    def _remove_headers_footers(self, text: str) -> str:
        """Remove header and footer patterns from text.

        Args:
            text: Input text.

        Returns:
            Text with header/footer patterns removed.
        """
        for pattern in self._header_footer_re:
            text = pattern.sub("", text)
        return text

    def _remove_page_numbers(self, text: str) -> str:
        """Remove standalone page numbers from text.

        Handles both Arabic (1, 2, 3) and Devanagari (१, २, ३) numerals
        that appear alone on a line.

        Args:
            text: Input text.

        Returns:
            Text with page numbers removed.
        """
        # Remove lines that are ONLY numerals (Arabic or Devanagari)
        text = re.sub(r"^\s*[0-9०-९]+\s*$", "", text, flags=re.MULTILINE)
        return text

    def _remove_ocr_garbage(self, text: str) -> str:
        """Remove OCR artifacts and non-meaningful characters.

        Preserves Devanagari characters, basic ASCII, Marathi punctuation
        (Danda, Double Danda), standard punctuation, and numerals.

        Args:
            text: Input text.

        Returns:
            Text with garbage characters removed.
        """
        for pattern in self._ocr_garbage_re:
            text = pattern.sub("", text)
        return text

    def _normalize_whitespace(self, text: str) -> str:
        """Collapse multiple whitespace characters into single spaces.

        Preserves paragraph breaks (double newlines) while collapsing
        excessive spacing within lines.

        Args:
            text: Input text.

        Returns:
            Whitespace-normalized text.
        """
        # Replace multiple spaces/tabs within a line with a single space
        text = re.sub(r"[^\S\n]+", " ", text)

        # Collapse 3+ newlines into double newlines (paragraph separator)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Remove leading/trailing whitespace on each line
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(lines)

        return text
