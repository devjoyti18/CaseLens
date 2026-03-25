"""
pipeline.py — Ingestion and query pipelines for CaseLens RAG
Lives at: <project-root>/rag/pipeline.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def ingestion_pipeline():
    """
    Full ingestion pipeline:
      1. Load PDFs from rag/dataStore/rawData/
      2. Chunk the documents (metadata preserved)
      3. Embed and store in ChromaDB vector store
    """
    # All imports done inside the function so app.py can import this
    # module without triggering heavy ML imports at startup.
    from rag.core.parser.document_loader import load_documents
    from rag.core.chunking.text_splitter import split_documents
    from rag.core.embedding.vector_store import create_vector_store

    base_dir = Path(__file__).resolve().parent          # <project-root>/rag/
    raw_data_path = str(base_dir / "dataStore" / "rawData")

    # 1. Load raw documents — legal metadata is extracted here
    documents = load_documents(raw_data_path)
    if not documents:
        raise ValueError(
            f"No documents found in {raw_data_path}. "
            "Upload PDFs first, then build the index."
        )

    # 2. Chunk — metadata stays attached to every chunk
    chunks = split_documents(documents)

    # 3. Embed and persist to ChromaDB
    create_vector_store(chunks)

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