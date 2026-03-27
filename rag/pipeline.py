"""
pipeline.py — Ingestion and query pipelines for CaseLens RAG
Lives at: <project-root>/rag/pipeline.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def ingestion_pipeline(raw_data_path: str = None, vector_store_path: str = None):
    """
    Full ingestion pipeline:
      1. Load PDFs from raw_data_path  (defaults to rag/dataStore/rawData/)
      2. Chunk the documents (metadata preserved)
      3. Embed and store in ChromaDB at vector_store_path

    When called from app.py each user session passes its own paths so that
    uploads and indexes are fully isolated between users.
    """
    from rag.core.parser.document_loader import load_documents
    from rag.core.chunking.text_splitter import split_documents
    from rag.core.embedding.vector_store import create_vector_store

    # Fall back to the legacy single-user paths if called without arguments
    # (e.g. from the CLI via  python -m rag.pipeline)
    if raw_data_path is None:
        base_dir = Path(__file__).resolve().parent   # <project-root>/rag/
        raw_data_path = str(base_dir / "dataStore" / "rawData")

    if vector_store_path is None:
        base_dir = Path(__file__).resolve().parent
        vector_store_path = str(base_dir / "dataStore" / "vectorStore")

    # 1. Load raw documents — legal metadata is extracted here
    documents = load_documents(raw_data_path)
    if not documents:
        raise ValueError(
            f"No documents found in {raw_data_path}. "
            "Upload PDFs first, then build the index."
        )

    # 2. Chunk — metadata stays attached to every chunk
    chunks = split_documents(documents)

    # 3. Embed and persist to ChromaDB at the session-specific path
    create_vector_store(chunks, persist_directory=vector_store_path)

    print(f"\n✅ Ingestion complete! {len(chunks)} chunks indexed from {len(documents)} document(s).")


def query_pipeline():
    """
    Interactive CLI query loop.
    Run directly:  python -m rag.pipeline
    """
    from rag.core.retrieval.similaritySearch import retrieve_chunks
    from rag.core.retrieval.responseGenerator import generate_answer

    print("CaseLens — type your question or 'quit' to exit.\n")
    while True:
        query = input("Question: ").strip()
        if query.lower() in ("quit", "exit", "q"):
            break
        if not query:
            continue

        chunks = retrieve_chunks(query)
        answer = generate_answer(query, chunks)
        print("\nAnswer:\n", answer, "\n")


if __name__ == "__main__":
    query_pipeline()