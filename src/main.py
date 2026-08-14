import typer
from extract import extract_repo

app = typer.Typer(help="RAG assistant for navigating a codebase.")


@app.command()
def index(repo: str):
    """Index a repo: extract symbols, embed them, store them."""
    symbols = extract_repo(repo)
    print(f"Found {len(symbols)} symbols in {repo}\n")
    for s in symbols:
        print(f" [{s.kind:8}] {s.name:30} {s.location()}")


@app.command()
def query(text: str):
    """Search the indexed codebase for a task or question."""
    print(f"TODO: query -> {text}")


if __name__ == "__main__":
    app()