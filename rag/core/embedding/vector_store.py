# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_chroma import Chroma
# from rag.config import VECTOR_STORE_DIR


# def create_vector_store(chunks):


#     #Create and persist Chroma vector store using HuggingFace embeddings
#     print("Creating embeddings and storing in ChromaDB...")
#     embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


#     print("--- Creating vector store ---")
#     vectorstore = Chroma.from_documents(
#         documents=chunks,
#         embedding=embedding_model,
#         persist_directory=VECTOR_STORE_DIR, 
#         collection_metadata={"hnsw:space": "cosine"}
#     )

#     print(f"Vector store created and saved to {VECTOR_STORE_DIR}")

#     return vectorstore



























# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_chroma import Chroma
# from rag.config import VECTOR_STORE_DIR

# # EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
# EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
# COLLECTION_NAME = "legal_cases"
# BATCH_SIZE = 100


# def create_vector_store(chunks):

#     print("Creating embeddings and storing in ChromaDB...")

#     # embedding_model = HuggingFaceEmbeddings(
#     #     model_name=EMBEDDING_MODEL,
#     #     model_kwargs={"device": "cpu"},
#     #     encode_kwargs={
#     #         "normalize_embeddings": True,  # required for cosine similarity
#     #         "batch_size": BATCH_SIZE,
#     #     },
#     # )

#     embedding_model = HuggingFaceEmbeddings(
#         model_name=EMBEDDING_MODEL,
#         model_kwargs={"device": "cpu"},
#         encode_kwargs={
#             "normalize_embeddings": True,
#             "batch_size": BATCH_SIZE,
#             "prompt": "Represent this legal document for retrieval: ",
#         },
#     )

#     # Filter metadata to only keep Chroma-safe scalar values (str, int, float, bool)
#     # Chroma rejects None values and will error on ingestion
#     for chunk in chunks:
#         chunk.metadata = {
#             k: v for k, v in chunk.metadata.items()
#             if isinstance(v, (str, int, float, bool))
#         }

#     print("--- Creating vector store ---")
#     vectorstore = Chroma.from_documents(
#         documents=chunks,
#         embedding=embedding_model,
#         persist_directory=VECTOR_STORE_DIR,
#         collection_name=COLLECTION_NAME,
#         collection_metadata={"hnsw:space": "cosine"},
#     )

#     print(f"Vector store created and saved to {VECTOR_STORE_DIR}")
#     print(f"  Total chunks embedded : {vectorstore._collection.count()}")

#     return vectorstore


import os
import shutil
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Lightweight model — only 90MB, works fine on Render free tier
# BAAI/bge-base-en-v1.5 is 440MB and causes OOM on free tier
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "legal_cases"


def create_vector_store(chunks, persist_directory=None):
    """
    Embed chunks and persist to ChromaDB.
    persist_directory is passed per-session from app.py.
    Falls back to config path when called from CLI.
    """
    if persist_directory is None:
        from rag.config import VECTOR_STORE_DIR
        persist_directory = str(VECTOR_STORE_DIR)

    print(f"Creating embeddings → {persist_directory}")

    embedding_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    # Clean metadata — ChromaDB only accepts str, int, float, bool (no None)
    for chunk in chunks:
        chunk.metadata = {
            k: (v if isinstance(v, (str, int, float, bool)) else str(v) if v is not None else "Unknown")
            for k, v in chunk.metadata.items()
        }

    # Clear old vector store so re-indexing always starts fresh
    if os.path.exists(persist_directory):
        shutil.rmtree(persist_directory)
    os.makedirs(persist_directory, exist_ok=True)

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=persist_directory,
        collection_name=COLLECTION_NAME,
        collection_metadata={"hnsw:space": "cosine"},
    )

    print(f"✅ Vector store created — {vectorstore._collection.count()} chunks indexed")
    return vectorstore