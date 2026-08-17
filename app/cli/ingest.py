"""Ingestion CLI Entry Point.

Run with: python -m app.cli.ingest

Executes the full ingestion pipeline (PDF → Clean → Chunk → Embed → Store)
and displays progress and statistics using Rich console output.
"""

import sys
import traceback
from dotenv import load_dotenv
load_dotenv()  # Load .env BEFORE any service imports (needed for GEMINI_API_KEY)

# Ensure UTF-8 output streams on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from app.config.constants import APP_NAME, APP_VERSION
from app.config.settings import get_settings
from app.embeddings.embedding_service import EmbeddingService
from app.ingestion.pdf_loader_ocr import PDFLoader
from app.preprocessing.chunker import TextChunker
from app.preprocessing.cleaner import TextCleaner
from app.services.ingest_service import IngestService
from app.utils.logger import get_logger
from app.vectorstore.chroma_service import ChromaService

logger = get_logger(__name__)
console = Console(force_terminal=True, legacy_windows=False)


def display_banner() -> None:
    """Display the application banner."""
    banner = Text()
    banner.append(f"\n  {APP_NAME}", style="bold cyan")
    banner.append(f" v{APP_VERSION}\n", style="dim")
    banner.append("  Textbook Ingestion Pipeline\n", style="italic")
    console.print(Panel(banner, border_style="cyan", padding=(0, 2)))


def display_results(result) -> None:
    """Display ingestion results in a Rich table.

    Args:
        result: ``IngestionResult`` from the ingestion service.
    """
    table = Table(
        title="📊 Ingestion Results",
        show_header=True,
        header_style="bold green",
        border_style="dim",
        padding=(0, 2),
    )
    table.add_column("Metric", style="bold", min_width=25)
    table.add_column("Value", style="cyan", min_width=20)

    table.add_row("Source File", result.source_file)
    table.add_row("Total Pages", str(result.total_pages))
    table.add_row("Extracted Pages", f"[green]{result.extracted_pages}[/green]")
    table.add_row("Empty Pages", f"[yellow]{result.empty_pages}[/yellow]")
    table.add_row("Failed Pages", f"[red]{result.failed_pages}[/red]")
    table.add_row("─" * 25, "─" * 20)
    table.add_row("Total Chunks", f"[bold cyan]{result.total_chunks}[/bold cyan]")
    table.add_row("Documents Stored", f"[bold green]{result.documents_stored}[/bold green]")
    table.add_row("Embedding Model", result.embedding_model)
    table.add_row("─" * 25, "─" * 20)
    table.add_row("PDF Load Time", result.pdf_load_time)
    table.add_row("Cleaning Time", result.cleaning_time)
    table.add_row("Chunking Time", result.chunking_time)
    table.add_row("Embed + Store Time", result.embedding_store_time)
    table.add_row("─" * 25, "─" * 20)
    table.add_row("Total Time", f"[bold]{result.total_time}[/bold]")

    console.print()
    console.print(table)
    console.print()
    console.print("[bold green]✅ Ingestion completed successfully![/bold green]")
    console.print()


def main() -> None:
    """Main entry point for the ingestion CLI."""
    display_banner()

    try:
        settings = get_settings()

        console.print(f"  PDF Path: [cyan]{settings.pdf_path}[/cyan]")
        console.print(f"  Chunk Size: [cyan]{settings.chunk_size}[/cyan]")
        console.print(f"  Chunk Overlap: [cyan]{settings.chunk_overlap}[/cyan]")
        console.print(f"  Embedding Model: [cyan]{settings.embedding_model_name}[/cyan]")
        console.print(f"  ChromaDB Dir: [cyan]{settings.chroma_persist_dir}[/cyan]")
        console.print()

        # Initialize services with dependency injection
        pdf_loader = PDFLoader(settings=settings)
        text_cleaner = TextCleaner(settings=settings)
        text_chunker = TextChunker(settings=settings)
        embedding_service = EmbeddingService(settings=settings)
        chroma_service = ChromaService(
            embedding_service=embedding_service,
            settings=settings,
        )

        # Create and run ingestion service
        ingest_service = IngestService(
            pdf_loader=pdf_loader,
            text_cleaner=text_cleaner,
            text_chunker=text_chunker,
            embedding_service=embedding_service,
            chroma_service=chroma_service,
            settings=settings,
        )

        result = ingest_service.run()
        display_results(result)

    except FileNotFoundError as exc:
        console.print(f"\n[bold red]❌ File Error:[/bold red] {exc}")
        console.print("[dim]Ensure the textbook PDF is placed in the data/ directory.[/dim]")
        logger.error("File not found: %s", exc)
        sys.exit(1)

    except RuntimeError as exc:
        console.print(f"\n[bold red]❌ Runtime Error:[/bold red] {exc}")
        logger.error("Runtime error: %s", exc)
        sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Ingestion interrupted by user.[/yellow]")
        sys.exit(130)

    except Exception as exc:
        console.print(f"\n[bold red]❌ Unexpected Error:[/bold red] {exc}")
        logger.error("Unexpected error: %s\n%s", exc, traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
