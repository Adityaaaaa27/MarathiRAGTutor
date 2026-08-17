"""Retrieval Debugger Module.

Provides debugging and evaluation tools for the retrieval pipeline.
Runs retrieval without the LLM to inspect which chunks are returned,
their scores, and metadata. Essential for tuning retrieval quality.
"""

from typing import Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from app.config.settings import Settings, get_settings
from app.embeddings.embedding_service import EmbeddingService
from app.utils.helpers import truncate_text
from app.utils.logger import get_logger
from app.vectorstore.chroma_service import ChromaService, SearchResult

logger = get_logger(__name__)
console = Console()


class RetrievalDebugger:
    """Debugger for inspecting retrieval results without LLM generation.

    Useful for:
    - Verifying chunk relevance for a given query
    - Tuning top-K and score thresholds
    - Inspecting metadata (page numbers, chapters)
    - Identifying retrieval quality issues

    Args:
        chroma_service: Initialized ``ChromaService``.
        settings: Application settings.
    """

    def __init__(
        self,
        chroma_service: ChromaService,
        settings: Optional[Settings] = None,
    ) -> None:
        self._chroma_service = chroma_service
        self._settings = settings or get_settings()

    def debug_query(
        self,
        query: str,
        k: Optional[int] = None,
        filters: Optional[dict[str, Any]] = None,
        show_content: bool = True,
    ) -> list[SearchResult]:
        """Run retrieval and display detailed results.

        Args:
            query: Search query text.
            k: Number of results. Defaults to settings value.
            filters: Optional metadata filters.
            show_content: Whether to display full chunk content.

        Returns:
            List of ``SearchResult`` objects.
        """
        top_k = k or self._settings.retriever_top_k

        console.print()
        console.print(
            Panel(
                f"[bold]{query}[/bold]",
                title="🔍 Debug Query",
                border_style="cyan",
            )
        )
        console.print(f"  Top-K: {top_k} | Filters: {filters or 'None'}")
        console.print()

        results = self._chroma_service.search(
            query=query, k=top_k, filter_dict=filters
        )

        if not results:
            console.print("[yellow]No results found.[/yellow]")
            return results

        # Summary table
        table = Table(
            title="Retrieved Chunks",
            show_header=True,
            header_style="bold magenta",
            border_style="dim",
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Score", style="cyan", width=10)
        table.add_column("Page", style="green", width=6)
        table.add_column("Chapter", style="yellow", width=20)
        table.add_column("Chunk ID", style="dim", width=30)
        table.add_column("Preview", style="white", min_width=40)

        for i, result in enumerate(results, 1):
            meta = result.metadata
            preview = truncate_text(result.page_content.replace("\n", " "), 80)
            table.add_row(
                str(i),
                f"{result.score:.4f}",
                str(meta.get("page_number", "?")),
                str(meta.get("chapter", "unknown")),
                str(meta.get("chunk_id", "")),
                preview,
            )

        console.print(table)

        # Full content display
        if show_content:
            console.print()
            for i, result in enumerate(results, 1):
                meta = result.metadata
                console.print(
                    Panel(
                        result.page_content,
                        title=f"Chunk {i} | Page {meta.get('page_number', '?')} | Score: {result.score:.4f}",
                        border_style="green" if i == 1 else "dim",
                        padding=(1, 2),
                    )
                )

        return results

    @staticmethod
    def create_from_settings(settings: Optional[Settings] = None) -> "RetrievalDebugger":
        """Factory method to create a debugger with initialized services.

        Args:
            settings: Application settings.

        Returns:
            Configured ``RetrievalDebugger`` instance.
        """
        settings = settings or get_settings()

        embedding_service = EmbeddingService(settings=settings)
        embedding_service.initialize()

        chroma_service = ChromaService(
            embedding_service=embedding_service,
            settings=settings,
        )
        chroma_service.create()

        return RetrievalDebugger(
            chroma_service=chroma_service,
            settings=settings,
        )
