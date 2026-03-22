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
from rag.config import VECTOR_STORE_DIR

EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
COLLECTION_NAME = "legal_cases"
BATCH_SIZE = 100


def create_vector_store(chunks):

    print("Creating embeddings and storing in ChromaDB...")

    embedding_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={
            "normalize_embeddings": True,
            "batch_size": BATCH_SIZE,
            "prompt": "Represent this legal document for retrieval: ",
        },
    )

    # Filter metadata to only keep Chroma-safe scalar values (str, int, float, bool)
    # Chroma rejects None values and will error on ingestion
    for chunk in chunks:
        chunk.metadata = {
            k: v for k, v in chunk.metadata.items()
            if isinstance(v, (str, int, float, bool))
        }

    # Clear existing vector store to prevent chunk accumulation across runs
    if os.path.exists(VECTOR_STORE_DIR):
        shutil.rmtree(VECTOR_STORE_DIR)

    # Always ensure directory exists (handles fresh clone with no vectorStore folder)
    os.makedirs(VECTOR_STORE_DIR, exist_ok=True)

    print("--- Creating vector store ---")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=str(VECTOR_STORE_DIR),
        collection_name=COLLECTION_NAME,
        collection_metadata={"hnsw:space": "cosine"},
    )

    print(f"Vector store created and saved to {VECTOR_STORE_DIR}")
    print(f"  Total chunks embedded : {vectorstore._collection.count()}")

    return vectorstore