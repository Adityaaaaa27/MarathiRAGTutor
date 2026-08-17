"""Multi-Standard Ingestion CLI Entry Point.

Ingests Maharashtra State Board Marathi textbooks for Standards 6, 7, 8, 9, and 10.
Uses Mistral Vision OCR (Pixtral-12B) with incremental JSON sidecar caching.
All standards are embedded and indexed into a unified ChromaDB collection with
metadata tags for filtered or cross-standard retrieval.

Run with:
    python -m app.cli.multi_ingest --standards all
    python -m app.cli.multi_ingest --standards 7
    python -m app.cli.multi_ingest --standards 6,7,8,9,10
"""

import argparse
import sys
import time
import traceback
from pathlib import Path

# Ensure UTF-8 output streams on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from app.config.constants import (
    APP_NAME,
    APP_VERSION,
    AVAILABLE_STANDARDS,
    DEFAULT_SUBJECT,
)
from app.config.settings import get_settings
from app.embeddings.embedding_service import EmbeddingService
from app.ingestion.pdf_loader_ocr import PDFLoader
from app.preprocessing.chunker import TextChunker
from app.preprocessing.cleaner import TextCleaner
from app.utils.helpers import format_elapsed
from app.utils.logger import get_logger
from app.vectorstore.chroma_service import ChromaService

logger = get_logger(__name__)
console = Console(force_terminal=True, legacy_windows=False)


def display_banner() -> None:
    """Display the multi-standard ingestion banner."""
    banner = Text()
    banner.append(f"\n  {APP_NAME}", style="bold cyan")
    banner.append(f" v{APP_VERSION}\n", style="dim")
    banner.append("  Multi-Standard Textbook Ingestion (Std. 6 - 10)\n", style="italic")
    console.print(Panel(banner, border_style="cyan", padding=(0, 2)))


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Ingest Marathi textbooks for Std 6-10")
    parser.add_argument(
        "--standards",
        type=str,
        default="all",
        help="Comma-separated standards to ingest (e.g., '6,7,8,9,10' or 'all' or '7')",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        default=False,
        help="Reset entire ChromaDB collection before ingesting",
    )
    return parser.parse_args()


def get_target_standards(standards_arg: str) -> list[int]:
    """Parse standards argument into a list of integers."""
    if standards_arg.strip().lower() == "all":
        return sorted(AVAILABLE_STANDARDS.keys())
    
    result = []
    for item in standards_arg.split(","):
        s = item.strip()
        if s.isdigit():
            val = int(s)
            if val in AVAILABLE_STANDARDS:
                result.append(val)
            else:
                console.print(f"[yellow]⚠️ Standard {val} not configured in AVAILABLE_STANDARDS. Skipping.[/yellow]")
    return sorted(result)


def _build_toc_chunks(standard: int, source_filename: str) -> list:
    """Build synthetic Table of Contents chunks for a given standard.

    These chunks ensure TOC / chapter-list queries always return accurate
    results, even when the PDF front pages have legacy font encoding issues.

    Args:
        standard: Grade/standard number (6 or 7).
        source_filename: Name of the source PDF file.

    Returns:
        List of LangChain Document objects with rich TOC content.
    """
    from langchain_core.documents import Document
    from app.config.constants import (
        META_PAGE_NUMBER, META_CHAPTER, META_CHUNK_ID,
        META_SOURCE, META_TEXTBOOK_ID, META_STANDARD, META_SUBJECT,
        AVAILABLE_STANDARDS,
    )

    std_info = AVAILABLE_STANDARDS.get(standard, {})
    textbook_id = std_info.get("textbook_id", f"mh_state_board_marathi_std_{standard}")

    base_meta = {
        META_SOURCE: source_filename,
        META_TEXTBOOK_ID: textbook_id,
        META_STANDARD: standard,
        META_SUBJECT: "Marathi",
    }

    # ── Standard 6 TOC ────────────────────────────────────────────────────────
    if standard == 6:
        toc_part1 = (
            "अनुक्रमणिका - इयत्ता सहावी मराठी पाठ्यपुस्तक (शिकू मराठी आनंदाने)\n\n"
            "भाग - १\n"
            "अ. क्र. पाठ/कविता - लेखक/कवी - पृष्ठ क्र.\n"
            "१. या भारतात बंधुभाव (प्रार्थना) - राष्ट्रसंत श्री तुकडोजी महाराज - पृष्ठ १\n"
            "२. चिमणीचं घरटं - अलका उमरणीकर - पृष्ठ २\n"
            "३. जिकडे तिकडे पाणीच पाणी (कविता) - शंकर वैद्य - पृष्ठ ७\n"
            "चित्रवाचन - पृष्ठ १०\n"
            "४. आम्ही महाराष्ट्रकन्या (कविता) - पद्मा गोळे - पृष्ठ १२\n"
            "५. आईचे पत्र - पृष्ठ १६\n\n"
            "भाग - २\n"
            "६. अमुचा बाग विकसनशील छान (कविता) - यशवंत देव - पृष्ठ २१\n"
            "७. आजोबांचा तीन पुड्यांचा डबा - अदिती देवधर - पृष्ठ २५\n"
            "८. नव्या युगाची गाणी (कविता) - वंदना विटणकर - पृष्ठ ३२\n"
            "९. निसर्गरम्य माथेरान - सुशील दुधाणे - पृष्ठ ३५\n"
            "अनुभव लेखन - पृष्ठ ३८\n"
        )
        toc_part2 = (
            "अनुक्रमणिका (भाग ३ व ४) - इयत्ता सहावी मराठी पाठ्यपुस्तक\n\n"
            "भाग - ३\n"
            "बातमी आकलन - पृष्ठ ४०\n"
            "१०. मी मोठा की लहान? - सुनंदा उमर्जी - पृष्ठ ४२\n"
            "११. गवतफुला रे! गवतफुला! (कविता) - इंदिरा संत - पृष्ठ ४६\n"
            "१२. जाहिरात - पृष्ठ ५०\n"
            "१३. गणितातील एक कूटप्रश्न - दिवाकर बापट - पृष्ठ ५५\n"
            "१४. सुगी (कविता) - संतोष आळंजरकर - पृष्ठ ६०\n\n"
            "भाग - ४\n"
            "१५. थोरांची ओळख:\n"
            "    (अ) डॉ. ए. पी. जे. अब्दुल कलाम - पृष्ठ ६४\n"
            "    (आ) लालबहादूर शास्त्री - जयसिंगराव राठोड - पृष्ठ ६५\n"
            "१६. मायबोली (कविता) - सुरेश भट - पृष्ठ ६६\n"
            "१७. आपली संस्कृती, आपल्या परंपरा - पृष्ठ ७१\n"
            "१८. नव्या तू (कविता) - राजेंद्र आरेकर - पृष्ठ ७७\n"
            "१९. विभूतींची भंबेरी - प्र. के. अत्रे - पृष्ठ ८१\n"
            "माझा अनुभव (अनुभव लेखन) - पृष्ठ ८७\n"
            "२०. विचारधन - पृष्ठ ८८\n"
        )
        toc_summary = (
            "या पाठ्यपुस्तकात (इयत्ता सहावी मराठी - शिकू मराठी आनंदाने) एकूण २० पाठ आणि कविता आहेत. "
            "यामध्ये प्रार्थना, कविता, कथा, पत्र, प्रवासवर्णन (निसर्गरम्य माथेरान), संवाद, जाहिरात, "
            "थोरांची ओळख आणि विचारधन यांचा समावेश आहे. "
            "पाठ्यपुस्तक चार भागांमध्ये (भाग १ ते ४) विभागलेले आहे. "
            "हे पाठ्यपुस्तक महाराष्ट्र राज्य पाठ्यपुस्तक निर्मिती व अभ्यासक्रम संशोधन मंडळ, पुणे यांनी प्रकाशित केले आहे."
        )
        return [
            Document(
                page_content=toc_part1,
                metadata={**base_meta, META_PAGE_NUMBER: 10,
                           META_CHAPTER: "अनुक्रमणिका (भाग १ व २)",
                           META_CHUNK_ID: f"{textbook_id}_toc_part1"},
            ),
            Document(
                page_content=toc_part2,
                metadata={**base_meta, META_PAGE_NUMBER: 10,
                           META_CHAPTER: "अनुक्रमणिका (भाग ३ व ४)",
                           META_CHUNK_ID: f"{textbook_id}_toc_part2"},
            ),
            Document(
                page_content=toc_summary,
                metadata={**base_meta, META_PAGE_NUMBER: 10,
                           META_CHAPTER: "अनुक्रमणिका - सारांश",
                           META_CHUNK_ID: f"{textbook_id}_toc_summary"},
            ),
        ]

    # ── Standard 7 TOC ────────────────────────────────────────────────────────
    if standard == 7:
        toc_part1 = (
            "अनुक्रमणिका - इयत्ता सातवी मराठी पाठ्यपुस्तक\n\n"
            "भाग - १\n"
            "अ. क्र. | पाठाचे नाव | लेखक/कवी | पृ. क्र.\n"
            "१. प्रार्थना - जगदीश खेबुडकर - पृष्ठ १\n"
            "२. श्यामचे बंधुप्रेम - सानेगुरुजी - पृष्ठ २\n"
            "३. माझ्या अंगणात (कविता) - ज्ञानेश्वर कोळी - पृष्ठ ७\n"
            "४. गोपाळाचे शौर्य - लक्ष्मीकमल गेडाम - पृष्ठ १०\n"
            "५. दादास पत्र / आम्ही सूचनाफलक वाचतो - पृष्ठ १५, १७\n"
            "६. टप् टप् पडती (कविता) - मंगेश पाडगावकर - पृष्ठ १८\n"
            "७. आजारी पडण्याचा प्रयोग / आपली समस्या आपले उपाय-१ / आम्ही जाहिरात वाचतो"
            " - डॉ. मा. मिरासदार - पृष्ठ २१, २६, २७\n"
        )
        toc_part2 = (
            "अनुक्रमणिका (भाग २) - इयत्ता सातवी मराठी पाठ्यपुस्तक\n\n"
            "भाग - २\n"
            "अ. क्र. | पाठाचे नाव | लेखक/कवी | पृ. क्र.\n"
            "८. शब्दांचे घर (कविता) - कल्याण इनामदार - पृष्ठ २८\n"
            "९. वाचनाचे वेड / आम्ही बातमी वाचतो - आशा पाटील - पृष्ठ ३१, ३५\n"
            "१०. पंडिता रामाबाई - डॉ. अनुपमा उजगरे - पृष्ठ ३६\n"
            "११. लेख (कविता) / आपली समस्या आपले उपाय-२"
            " - अस्मिता जोगदंडे-चांदणे - पृष्ठ ४०, ४३\n"
            "१२. रोजनिशी - पृष्ठ ४४\n"
            "१३. अदलाबदल - पन्नालाल पटेल - पृष्ठ ४७\n"
            "१४. संतवाणी - संत जनाबाई, संत तुकाराम - पृष्ठ ५२\n"
        )
        toc_summary = (
            "या पाठ्यपुस्तकात (इयत्ता सातवी मराठी) एकूण १४ पाठ आणि कविता आहेत. "
            "भाग १ मध्ये: प्रार्थना, श्यामचे बंधुप्रेम, माझ्या अंगणात, गोपाळाचे शौर्य, दादास पत्र, "
            "टप् टप् पडती, आजारी पडण्याचा प्रयोग. "
            "भाग २ मध्ये: शब्दांचे घर, वाचनाचे वेड, पंडिता रामाबाई, लेख, रोजनिशी, अदलाबदल, संतवाणी. "
            "हे पाठ्यपुस्तक महाराष्ट्र राज्य पाठ्यपुस्तक निर्मिती व अभ्यासक्रम संशोधन मंडळ, पुणे यांनी प्रकाशित केले आहे."
        )
        return [
            Document(
                page_content=toc_part1,
                metadata={**base_meta, META_PAGE_NUMBER: 11,
                           META_CHAPTER: "अनुक्रमणिका (भाग १)",
                           META_CHUNK_ID: f"{textbook_id}_toc_part1"},
            ),
            Document(
                page_content=toc_part2,
                metadata={**base_meta, META_PAGE_NUMBER: 11,
                           META_CHAPTER: "अनुक्रमणिका (भाग २)",
                           META_CHUNK_ID: f"{textbook_id}_toc_part2"},
            ),
            Document(
                page_content=toc_summary,
                metadata={**base_meta, META_PAGE_NUMBER: 11,
                           META_CHAPTER: "अनुक्रमणिका - सारांश",
                           META_CHUNK_ID: f"{textbook_id}_toc_summary"},
            ),
        ]

    # ── Standard 8 TOC ────────────────────────────────────────────────────────
    if standard == 8:
        toc_part1 = (
            "अनुक्रमणिका - इयत्ता आठवी मराठी पाठ्यपुस्तक (बालभारती)\n\n"
            "भाग - १\n"
            "अ. क्र. | पाठाचे नाव | लेखक/कवी | पृ. क्र.\n"
            "१. भारत अमुचा देश... (गीत) - शरद कांबळे - पृष्ठ १\n"
            "२. चिव चिव चिमण्या... - विजय तेंडुलकर - पृष्ठ २\n"
            "३. जिकडे तिकडे पाणीच पाणी (कविता) - शंकर वैद्य - पृष्ठ ७\n"
            "४. सावलीतून जा आणि सावलीतून ये - सु. ह. जोशी - पृष्ठ ९\n"
            "५. विश्वविश्वात शास्त्रज्ञ - स्टीफन हॉकिंग - डॉ. किशोर पवार, नलिनी पवार - पृष्ठ १४\n"
            "६. कोळ्याची पोर (कविता) - सुरेखा गावडे - पृष्ठ १८\n"
        )
        toc_part2 = (
            "अनुक्रमणिका (भाग २) - इयत्ता आठवी मराठी पाठ्यपुस्तक\n\n"
            "भाग - २\n"
            "अ. क्र. | पाठाचे नाव | लेखक/कवी | पृ. क्र.\n"
            "७. ध्येयपूर्तीचा ध्यास - लक्ष्मण लोंढे - पृष्ठ २१\n"
            "८. पाखरांचे मागणे (कविता) - प्रेमचंद अहिराव - पृष्ठ २७\n"
            "९. भूमिगत - मुमताज रहिमतपुरे - पृष्ठ ३०\n"
            "१०. जीवन सुंदर करू! (कविता) - शं. ल. नाईक - पृष्ठ ३५\n"
            "११. प्राणी आणि आपण - ललितगौरी डांगे - पृष्ठ ३९\n"
            "१२. संतवाणी - (अ) संत एकनाथ (आ) संत श्रीनिवासा (श्रीनिलोबाराय) - पृष्ठ ४२\n"
        )
        toc_summary = (
            "या पाठ्यपुस्तकात (इयत्ता आठवी मराठी) एकूण १२ पाठ आणि कविता आहेत. "
            "भाग १ मध्ये: भारत अमुचा देश, चिव चिव चिमण्या, जिकडे तिकडे पाणीच पाणी, सावलीतून जा आणि सावलीतून ये, "
            "विश्वविश्वात शास्त्रज्ञ - स्टीफन हॉकिंग, कोळ्याची पोर. "
            "भाग २ मध्ये: ध्येयपूर्तीचा ध्यास, पाखरांचे मागणे, भूमिगत, जीवन सुंदर करू!, प्राणी आणि आपण, संतवाणी. "
            "हे पाठ्यपुस्तक महाराष्ट्र राज्य पाठ्यपुस्तक निर्मिती व अभ्यासक्रम संशोधन मंडळ, पुणे यांनी प्रकाशित केले आहे."
        )
        return [
            Document(
                page_content=toc_part1,
                metadata={**base_meta, META_PAGE_NUMBER: 11,
                           META_CHAPTER: "अनुक्रमणिका (भाग १)",
                           META_CHUNK_ID: f"{textbook_id}_toc_part1"},
            ),
            Document(
                page_content=toc_part2,
                metadata={**base_meta, META_PAGE_NUMBER: 11,
                           META_CHAPTER: "अनुक्रमणिका (भाग २)",
                           META_CHUNK_ID: f"{textbook_id}_toc_part2"},
            ),
            Document(
                page_content=toc_summary,
                metadata={**base_meta, META_PAGE_NUMBER: 11,
                           META_CHAPTER: "अनुक्रमणिका - सारांश",
                           META_CHUNK_ID: f"{textbook_id}_toc_summary"},
            ),
        ]

    return []


def ingest_standard(
    standard: int,
    text_cleaner: TextCleaner,
    text_chunker: TextChunker,
    settings,
) -> list:
    """Run OCR extraction, cleaning, and chunking for a single standard."""
    std_info = AVAILABLE_STANDARDS[standard]
    pdf_path = settings.pdf_path.parent / std_info["pdf_filename"]
    cache_path = settings.pdf_path.parent / std_info["cache_filename"]

    if not pdf_path.exists():
        # Fallback check
        fallback_pdf = settings.pdf_path.parent.parent / std_info["pdf_filename"]
        if fallback_pdf.exists():
            pdf_path = fallback_pdf
        else:
            raise FileNotFoundError(f"PDF file not found for Standard {standard}: {pdf_path}")

    console.print(f"\n[bold green]📚 Processing {std_info['name']} — {std_info['title']}[/bold green]")
    console.print(f"  PDF File: [cyan]{pdf_path.name}[/cyan]")
    console.print(f"  Cache File: [cyan]{cache_path.name}[/cyan]")

    # 1. OCR Extraction
    loader = PDFLoader(settings=settings, standard=standard, use_cache=True)
    extraction = loader.load(pdf_path=pdf_path, cache_path=cache_path)

    # 2. Text Cleaning
    pages = [
        {"page_number": p.page_number, "text": p.text}
        for p in extraction.pages
        if not p.is_empty and not p.error
    ]
    cleaned_pages = text_cleaner.clean_pages(pages)

    # 3. Chunking with standard tags
    chunks = text_chunker.chunk_pages(
        cleaned_pages,
        source_filename=pdf_path.name,
        standard=standard,
        textbook_id=std_info["textbook_id"],
    )

    # 4. Inject synthetic TOC chunks so chapter-list queries always work
    toc_chunks = _build_toc_chunks(standard, pdf_path.name)
    chunks.extend(toc_chunks)
    console.print(f"  📋 [dim]Added {len(toc_chunks)} synthetic TOC chunks for Std {standard}[/dim]")

    console.print(f"  ✅ [green]{len(chunks)} chunks created from {extraction.extracted_pages} pages[/green]")
    return chunks



def main() -> None:
    """Main CLI entry point for multi-standard ingestion."""
    display_banner()
    args = parse_args()
    target_standards = get_target_standards(args.standards)

    if not target_standards:
        console.print("[bold red]❌ No valid standards selected for ingestion.[/bold red]")
        sys.exit(1)

    console.print(f"Target Standards: [bold cyan]{target_standards}[/bold cyan]")
    total_start = time.perf_counter()

    try:
        settings = get_settings()
        text_cleaner = TextCleaner(settings=settings)
        text_chunker = TextChunker(settings=settings)
        embedding_service = EmbeddingService(settings=settings)

        if not embedding_service.is_initialized:
            console.print("\n[cyan]Initializing Multilingual Embedding Service...[/cyan]")
            embedding_service.initialize()

        chroma_service = ChromaService(
            embedding_service=embedding_service,
            settings=settings,
        )

        # Reset Chroma collection if requested or ingesting all from scratch
        if args.reset or (args.standards.strip().lower() == "all" and 6 in target_standards):
            console.print("[yellow]Resetting ChromaDB collection for fresh multi-standard index...[/yellow]")
            chroma_service.reset_collection()
            chroma_service.create()
        else:
            chroma_service.create()

        total_chunks_all = []
        standard_stats = {}

        for std in target_standards:
            std_start = time.perf_counter()
            chunks = ingest_standard(std, text_cleaner, text_chunker, settings)
            total_chunks_all.extend(chunks)
            
            # Store in ChromaDB per standard to avoid huge memory spike
            console.print(f"  Adding {len(chunks)} documents to ChromaDB for Std {std}...")
            chroma_service.add_documents(chunks)
            chroma_service.persist()

            standard_stats[std] = {
                "chunks": len(chunks),
                "time": format_elapsed(time.perf_counter() - std_start),
            }

        # Summary Table
        table = Table(
            title="📊 Multi-Standard Ingestion Summary",
            show_header=True,
            header_style="bold green",
            border_style="dim",
            padding=(0, 2),
        )
        table.add_column("इयत्ता (Standard)", style="bold", min_width=20)
        table.add_column("Chunks", style="cyan", min_width=12)
        table.add_column("Processing Time", style="green", min_width=16)

        for std, stats in standard_stats.items():
            std_name = AVAILABLE_STANDARDS[std]["name"]
            table.add_row(std_name, str(stats["chunks"]), stats["time"])

        table.add_row("─" * 20, "─" * 12, "─" * 16)
        table.add_row(
            "[bold]Total Chunks[/bold]",
            f"[bold green]{len(total_chunks_all)}[/bold green]",
            format_elapsed(time.perf_counter() - total_start),
        )

        console.print()
        console.print(table)
        console.print()
        console.print("[bold green]✅ All selected standards ingested successfully![/bold green]\n")

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Ingestion cancelled by user.[/yellow]")
        sys.exit(130)
    except Exception as exc:
        console.print(f"\n[bold red]❌ Ingestion failed:[/bold red] {exc}")
        logger.error("Multi-standard ingestion failed: %s\n%s", exc, traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
