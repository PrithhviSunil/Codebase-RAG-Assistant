from sentence_transformers import SentenceTransformer
import chromadb

# The "fingerprint machine" — loaded once. First run downloads ~90MB.
_model = SentenceTransformer("all-MiniLM-L6-v2")

# Chroma client that persists to disk in ./chroma
_client = chromadb.PersistentClient(path="chroma")


def embed(texts: list[str]) -> list[list[float]]:
    """Turn a list of text strings into a list of vectors."""
    return _model.encode(texts).tolist()


def store_symbols(symbols) -> int:
    """Embed each symbol's source and save it to Chroma with metadata."""
    
    try:
        _client.delete_collection("symbols")
    except Exception:
        pass
    collection = _client.create_collection("symbols")

    ids       = [f"{s.path}:{s.start_line}:{s.name}" for s in symbols]
    documents = [s.source for s in symbols]
    metadatas = [
        {"name": s.name, "kind": s.kind, "path": s.path, "start_line": s.start_line}
        for s in symbols
    ]
    vectors = embed(documents)

    collection.add(ids=ids, embeddings=vectors, documents=documents, metadatas=metadatas)
    return collection.count()

def search(question: str, n: int = 5):
    """Embed the question and return the n nearest symbols from Chroma."""
    collection = _client.get_collection("symbols")
    query_vec = embed([question])          # same model as indexing -> same space
    res = collection.query(query_embeddings=query_vec, n_results=n)

    hits = []
    for i in range(len(res["ids"][0])):
        m = res["metadatas"][0][i]
        hits.append({
            "name": m["name"],
            "kind": m["kind"],
            "location": f'{m["path"]}:{m["start_line"]}',
            "distance": res["distances"][0][i],
            "source": res["documents"][0][i],
        })
    return hits