"""Query CLI Entry Point.

Run with: python -m app.cli.query

Provides an interactive REPL for querying the Marathi RAG tutor.
Displays retrieved chunks, similarity scores, page numbers,
and the generated answer with Rich formatting.
"""

import sys
import traceback

# Ensure UTF-8 output streams on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from app.chains.rag_chain import QueryResult
from app.config.constants import APP_NAME, APP_VERSION
from app.services.query_service import QueryService
from app.utils.helpers import truncate_text
from app.utils.logger import get_logger

logger = get_logger(__name__)
console = Console(force_terminal=True, legacy_windows=False)


def display_banner() -> None:
    """Display the application banner."""
    banner = Text()
    banner.append(f"\n  {APP_NAME}", style="bold cyan")
    banner.append(f" v{APP_VERSION}\n", style="dim")
    banner.append("  Interactive Query Interface\n", style="italic")
    banner.append("  Type 'exit' or 'quit' to stop.\n", style="dim italic")
    console.print(Panel(banner, border_style="cyan", padding=(0, 2)))


def display_retrieved_chunks(result: QueryResult) -> None:
    """Display retrieved chunks in a Rich table.

    Args:
        result: The query result containing retrieved chunks.
    """
    if not result.retrieved_chunks:
        console.print("[yellow]No chunks retrieved.[/yellow]")
        return

    table = Table(
        title="📄 Retrieved Chunks",
        show_header=True,
        header_style="bold magenta",
        border_style="dim",
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Score", style="cyan", width=10)
    table.add_column("Page", style="green", width=6)
    table.add_column("Chapter", style="yellow", width=20)
    table.add_column("Preview", style="white", min_width=50)

    for i, chunk in enumerate(result.retrieved_chunks, 1):
        preview = truncate_text(chunk.content.replace("\n", " "), 100)
        table.add_row(
            str(i),
            f"{chunk.score:.4f}",
            str(chunk.page_number),
            chunk.chapter,
            preview,
        )

    console.print(table)


def display_answer(result: QueryResult) -> None:
    """Display the generated answer with formatting.

    Args:
        result: The query result containing the answer.
    """
    console.print()
    console.print(
        Panel(
            Markdown(result.answer),
            title="🎓 उत्तर (Answer)",
            border_style="green",
            padding=(1, 2),
        )
    )
    console.print()


def run_interactive_loop(query_service: QueryService) -> None:
    """Run the interactive query REPL.

    Args:
        query_service: Initialized ``QueryService`` instance.
    """
    while True:
        try:
            console.print("[bold cyan]>[/bold cyan] ", end="")
            question = input().strip()

            if not question:
                continue

            if question.lower() in ("exit", "quit", "q", "बंद"):
                console.print("[dim]Goodbye! 👋[/dim]")
                break

            console.print()

            # Execute query
            with console.status("[cyan]Thinking...[/cyan]", spinner="dots"):
                result = query_service.ask(question)

            # Display results
            display_answer(result)

        except KeyboardInterrupt:
            console.print("\n[dim]Goodbye! 👋[/dim]")
            break

        except Exception as exc:
            console.print(f"\n[bold red]❌ Error:[/bold red] {exc}")
            logger.error("Query error: %s", exc)
            console.print("[dim]Please try again.[/dim]\n")


def main() -> None:
    """Main entry point for the query CLI."""
    display_banner()

    try:
        console.print("[cyan]Initializing services...[/cyan]")
        console.print()

        query_service = QueryService()

        with console.status("[cyan]Loading models and connecting to vector store...[/cyan]", spinner="dots"):
            query_service.initialize()

        console.print("[bold green]✅ Ready! Ask your questions below.[/bold green]\n")

        run_interactive_loop(query_service)

    except ValueError as exc:
        console.print(f"\n[bold red]❌ Configuration Error:[/bold red] {exc}")
        logger.error("Configuration error: %s", exc)
        sys.exit(1)

    except RuntimeError as exc:
        console.print(f"\n[bold red]❌ Runtime Error:[/bold red] {exc}")
        logger.error("Runtime error: %s", exc)
        sys.exit(1)

    except Exception as exc:
        console.print(f"\n[bold red]❌ Unexpected Error:[/bold red] {exc}")
        logger.error("Unexpected error: %s\n%s", exc, traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
