# Codebase RAG Assistant

A CLI tool that answers natural-language questions about a codebase by retrieving the most relevant functions and classes — with exact `file:line` locations — instead of guessing or grepping.

Ask something like *"how does retry logic work"* and get back ranked, real code locations, even when the answer doesn't contain the word "retry."

## Why
Most "chat with your codebase" tools chunk source files into fixed-size blocks of text before embedding them. That splits functions in half and loses structure. This project instead parses source with **tree-sitter** and chunks by **symbol** — one function or class per chunk — so every retrieved result is a complete, meaningful unit with a precise location.


## How it works

1. **Extract** — walk a repo, parse each Python file with tree-sitter, and pull out every function, class, and method with its qualified name (e.g. `AuthManager.login`) and exact `file:line` range.
2. **Embed** — turn each symbol's source into a vector using a local `sentence-transformers` model (`all-MiniLM-L6-v2`). Runs fully offline, no API keys.
3. **Store** — persist symbols and their vectors in a local ChromaDB collection.
4. **Search** — embed the user's question with the same model, and retrieve the nearest symbols by vector similarity, ranked with their source locations.
5. **MCP server** — the same search is exposed as an MCP tool, so AI coding assistants like Claude Code can call it directly to ground their answers in real source locations.

## Install

```bash
pip install tree-sitter tree-sitter-python sentence-transformers chromadb typer rich
```

## Usage

Index a repository:

```bash
python src/main.py index /path/to/repo
```

Query it:

```bash
python src/main.py query "how does the library retry failed requests"
```

Each result shows the symbol's kind, qualified name, `file:line` location, and a source preview.

## MCP server

Exposes the same retrieval as a tool (`search_code`) that MCP-compatible clients like Claude Code can call directly.

```bash
pip install "mcp[cli]"
claude mcp add codebase-rag -- python src/mcp_server.py
```

Once registered, an assistant with access to this tool can answer questions about the indexed repo using real, current source locations instead of relying on memory.

## Project structure


```
src/
  extract.py      # tree-sitter symbol extraction
  store.py        # embedding + ChromaDB storage/search
  main.py         # Typer CLI (index, query)
  mcp_server.py   # MCP server exposing search as a tool
```

## Status

Working end to end on real repositories (tested on `requests`, 800+ symbols extracted and searchable). Currently supports Python only.

## Roadmap

- [ ] Multi-language support (JavaScript/TypeScript via tree-sitter grammars)
- [ ] Dependency/call-graph aware retrieval
- [ ] `--no-tests` flag to exclude test files from results
- [ ] Installable pip package
- [ ] Hybrid search (embeddings + keyword/symbol-name matching)

## Stack

Python, tree-sitter, ChromaDB, sentence-transformers, Typer, Rich, MCP
