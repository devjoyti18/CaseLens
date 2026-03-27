from pathlib import Path

# This file lives at:  <project-root>/rag/config.py
# BASE_DIR resolves to: <project-root>/rag/
BASE_DIR = Path(__file__).resolve().parent

# ── Legacy single-user paths (used by CLI / direct pipeline calls only) ────────
# When running through the Flask server, each user session gets its own
# paths passed directly into ingestion_pipeline() and retrieve_chunks().

VECTOR_STORE_DIR = BASE_DIR / "dataStore" / "vectorStore"
VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)