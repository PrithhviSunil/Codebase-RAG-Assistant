

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path

import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Node

PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)


@dataclass
class Symbol:
    kind: str            # "function" | "class" | "method"
    name: str            # qualified: "MyClass.my_method"
    path: str            # repo-relative file path
    start_line: int      # 1-indexed, inclusive
    end_line: int        # 1-indexed, inclusive
    source: str          # raw source text of the symbol (for embedding later)

    def location(self) -> str:
        return f"{self.path}:{self.start_line}"


def _node_name(node: Node, src: bytes) -> str:
    """Get the identifier a function/class definition binds."""
    name_node = node.child_by_field_name("name")
    if name_node is None:
        return "<anonymous>"
    return src[name_node.start_byte:name_node.end_byte].decode("utf-8", "replace")


def _walk(node: Node, src: bytes, path: str, symbols: list[Symbol], class_ctx: str | None = None):
    for child in node.children:
        if child.type == "class_definition":
            name = _node_name(child, src)
            symbols.append(Symbol(
                kind="class",
                name=name,
                path=path,
                start_line=child.start_point[0] + 1,
                end_line=child.end_point[0] + 1,
                source=src[child.start_byte:child.end_byte].decode("utf-8", "replace"),
            ))
            # recurse into class body with class context so methods get qualified names
            _walk(child, src, path, symbols, class_ctx=name)

        elif child.type == "function_definition":
            name = _node_name(child, src)
            qualified = f"{class_ctx}.{name}" if class_ctx else name
            symbols.append(Symbol(
                kind="method" if class_ctx else "function",
                name=qualified,
                path=path,
                start_line=child.start_point[0] + 1,
                end_line=child.end_point[0] + 1,
                source=src[child.start_byte:child.end_byte].decode("utf-8", "replace"),
            ))
            # recurse to catch nested functions, but drop class context
            _walk(child, src, path, symbols, class_ctx=None)

        else:
            _walk(child, src, path, symbols, class_ctx=class_ctx)


def extract_file(file_path: Path, repo_root: Path) -> list[Symbol]:
    src = file_path.read_bytes()
    tree = parser.parse(src)
    rel = str(file_path.relative_to(repo_root))
    symbols: list[Symbol] = []
    _walk(tree.root_node, src, rel, symbols)
    return symbols


def extract_repo(repo_root: str | Path, ignore: set[str] = frozenset({".git", "__pycache__", ".venv", "venv", "node_modules"})) -> list[Symbol]:
    repo_root = Path(repo_root).resolve()
    all_symbols: list[Symbol] = []
    for py_file in repo_root.rglob("*.py"):
        if any(part in ignore for part in py_file.parts):
            continue
        try:
            all_symbols.extend(extract_file(py_file, repo_root))
        except Exception as e:
            print(f"  ! skipped {py_file}: {e}")
    return all_symbols


if __name__ == "__main__":
    import sys
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    syms = extract_repo(root)
    print(f"Found {len(syms)} symbols in {root}\n")
    for s in syms:
        print(f"  [{s.kind:8}] {s.name:30} {s.location()}  ({s.end_line - s.start_line + 1} lines)")