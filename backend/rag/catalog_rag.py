"""
CatalogRAG — semantic search over Albertsons product catalog.

Ingests the `products` table from DuckDB into a ChromaDB vector store
using the all-MiniLM-L6-v2 sentence-transformer model.

Usage:
  # Build the index (run once from backend/):
  python rag/catalog_rag.py

  # Query the index from any agent:
  from rag.catalog_rag import search_catalog
  results = search_catalog("plant-based protein snack", n_results=5)
"""

import os
import sys
from pathlib import Path

import duckdb
import chromadb
from sentence_transformers import SentenceTransformer

# ── Config ──────────────────────────────────────────────────────────────────

CHROMA_DIR = Path(__file__).parent.parent / "db" / "chroma"
COLLECTION_NAME = "product_catalog"
MODEL_NAME = "all-MiniLM-L6-v2"


def _resolve_db_path() -> Path:
    """Locate aci.duckdb — same logic as db/queries.py."""
    if env := os.environ.get("ACI_DB_PATH"):
        return Path(env)
    here = Path(__file__).resolve().parent
    for _ in range(6):
        for candidate in (here / "db" / "aci.duckdb", here / "aci.duckdb"):
            if candidate.exists():
                return candidate
        here = here.parent
    raise FileNotFoundError("Cannot find aci.duckdb — set ACI_DB_PATH env var.")


# ── Ingestion ────────────────────────────────────────────────────────────────

def build_index() -> None:
    """
    Read products from DuckDB, embed with all-MiniLM-L6-v2,
    and upsert into ChromaDB.  Safe to re-run — ChromaDB upserts.
    """
    db_path = _resolve_db_path()
    print(f"[catalog_rag] Loading products from {db_path}")

    con = duckdb.connect(str(db_path), read_only=True)
    rows = con.execute(
        """
        SELECT
            upc_id,
            upc_dsc,
            COALESCE(brand_nm, '') AS brand_nm,
            COALESCE(sub_category_nm, '') AS sub_category_nm,
            COALESCE(category_nm, '') AS category_nm,
            COALESCE(department_nm, '') AS department_nm
        FROM products
        ORDER BY upc_id
        """
    ).fetchall()
    con.close()

    if not rows:
        print("[catalog_rag] No products found — skipping index build.")
        return

    print(f"[catalog_rag] Embedding {len(rows)} products with {MODEL_NAME}…")
    model = SentenceTransformer(MODEL_NAME)

    ids, documents, metadatas = [], [], []
    for upc_id, upc_dsc, brand_nm, sub_cat, cat, dept in rows:
        text = f"{upc_dsc} {brand_nm} {sub_cat} {cat} {dept}".strip()
        ids.append(str(upc_id))
        documents.append(text)
        metadatas.append({
            "upc_id": str(upc_id),
            "upc_dsc": upc_dsc or "",
            "brand_nm": brand_nm,
            "sub_category_nm": sub_cat,
            "category_nm": cat,
            "department_nm": dept,
        })

    embeddings = model.encode(documents, show_progress_bar=True).tolist()

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    # Upsert in batches of 100 to stay within ChromaDB limits
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        collection.upsert(
            ids=ids[i : i + batch_size],
            documents=documents[i : i + batch_size],
            embeddings=embeddings[i : i + batch_size],
            metadatas=metadatas[i : i + batch_size],
        )

    print(f"[catalog_rag] Indexed {len(ids)} products → {CHROMA_DIR}")


# ── Query ────────────────────────────────────────────────────────────────────

_model: SentenceTransformer | None = None
_collection = None


def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def search_catalog(query: str, n_results: int = 5) -> list[dict]:
    """
    Semantic product search.

    Args:
        query:     Free-text search string (e.g. "plant-based burger")
        n_results: Maximum number of results to return

    Returns:
        List of dicts with keys: upc_id, upc_dsc, brand_nm,
        sub_category_nm, category_nm, department_nm, score
    """
    collection = _get_collection()

    if collection.count() == 0:
        # Index not yet built — return empty rather than crash
        return []

    model = _get_model()
    embedding = model.encode([query]).tolist()

    results = collection.query(
        query_embeddings=embedding,
        n_results=min(n_results, collection.count()),
        include=["metadatas", "distances"],
    )

    output = []
    for meta, dist in zip(
        results["metadatas"][0], results["distances"][0]
    ):
        output.append({
            **meta,
            "score": round(1 - dist, 4),  # cosine similarity (higher = better)
        })

    return output


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    build_index()

    # Quick smoke-test
    print("\n[catalog_rag] Smoke-test: 'organic plant based protein'")
    hits = search_catalog("organic plant based protein", n_results=3)
    for h in hits:
        print(f"  {h['score']:.3f}  {h['upc_dsc']}  ({h['brand_nm']})")
