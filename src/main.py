import typer
from extract import extract_repo
from store import store_symbols, search

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()

app = typer.Typer(help="RAG assistant for navigating a codebase.")


@app.command()
def index(repo: str):
    """Index a repo: extract symbols, embed them, store them."""
    symbols = extract_repo(repo)
    print(f"Extracted {len(symbols)} symbols. Embedding + storing...")
    count = store_symbols(symbols)
    print(f"Stored {count} symbols in Chroma.")


@app.command()
def query(text: str, n: int = 5):
    """Search the indexed codebase for a task or question."""
    hits = search(text, n)
    if not hits:
        console.print("[yellow]No results. Did you run `index` first?[/yellow]")
        return

    console.print(f"\n[bold]Top {len(hits)} matches for:[/bold] [cyan]{text}[/cyan]\n")
    for rank, h in enumerate(hits, 1):
        header = f"[bold green]{rank}. {h['name']}[/bold green]  [dim]({h['kind']})[/dim]  →  [yellow]{h['location']}[/yellow]"
        console.print(header)
        # show first ~8 lines of the matched symbol as a preview
        preview = "\n".join(h["source"].splitlines()[:8])
        console.print(Syntax(preview, "python", theme="ansi_dark", line_numbers=False))
        console.print()

if __name__ == "__main__":
    app()

