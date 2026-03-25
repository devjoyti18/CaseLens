from pathlib import Path

# This file lives at:  <project-root>/rag/config.py
# BASE_DIR resolves to: <project-root>/rag/
BASE_DIR = Path(__file__).resolve().parent

# Correct path: <project-root>/rag/dataStore/vectorStore/
VECTOR_STORE_DIR = BASE_DIR / "dataStore" / "vectorStore"

# Ensure the directory exists so ChromaDB never throws on first run
VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)