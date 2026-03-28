# from langchain_chroma import Chroma
# from langchain_huggingface import HuggingFaceEmbeddings
# from rag.config import VECTOR_STORE_DIR


# # Load embeddings + vector DB once
# embedding_model = HuggingFaceEmbeddings(
#     model_name="sentence-transformers/all-MiniLM-L6-v2"
# )

# db = Chroma(
#     persist_directory=VECTOR_STORE_DIR,
#     embedding_function= embedding_model,
#     collection_metadata={"hnsw:space": "cosine"}
# )


# #Custom retriever with similarity score threshold
# retriever = db.as_retriever(
#     search_type="similarity_score_threshold",
#     search_kwargs={
#         "k": 3,
#         "score_threshold": 0.3
#     }
# )



# def retrieve_chunks(query: str):

#     #Retrieve relevant document chunks for a given query
#     relevant_docs = retriever.invoke(query)

#     print(f"User Query: {query}")
    
#     # Display results
#     print("--- Context ---")
#     for i, doc in enumerate(relevant_docs, 1):
#         print(f"Document {i}:\n{doc.page_content}\n")

#     return relevant_docs




# # # Synthetic Questions: 

# # # “What is the definition of ‘Convertible Securities’ in this agreement?”

# # # “Which section explains the rights of non-signing holders?”

# # # “Where does the agreement describe the form of amended and restated certificate of incorporation?”

# # # “What exhibits are attached to this Stock Purchase Agreement?”

# # # “Which section defines the term ‘Purchasers’?”







































# from langchain_chroma import Chroma
# from langchain_huggingface import HuggingFaceEmbeddings
# from rag.config import VECTOR_STORE_DIR

# EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
# COLLECTION_NAME = "legal_cases"

# # Load embeddings + vector DB once
# embedding_model = HuggingFaceEmbeddings(
#     model_name=EMBEDDING_MODEL,
#     model_kwargs={"device": "cpu"},
#     encode_kwargs={
#         "normalize_embeddings": True,
#         "batch_size": 32,
#         "prompt": "Represent this legal query for retrieving relevant case documents: ",
#     },
# )

# # db = Chroma(
# #     persist_directory=VECTOR_STORE_DIR,
# #     embedding_function=embedding_model,
# #     collection_name=COLLECTION_NAME,
# #     collection_metadata={"hnsw:space": "cosine"},
# # )

# db = Chroma(
#     persist_directory=VECTOR_STORE_DIR,
#     embedding_function=embedding_model,
#     collection_name="legal_cases",          # add this
#     collection_metadata={"hnsw:space": "cosine"},
# )


# # retriever = db.as_retriever(
# #     search_type="mmr",
# #     search_kwargs={
# #         "k": 8,
# #         "fetch_k": 40,
# #         "lambda_mult": 0.7,
# #     },
# # )

# retriever = db.as_retriever(
#     search_type="similarity_score_threshold",
#     search_kwargs={
#         "score_threshold": 0.3,  # only return chunks above this similarity
#         "k": 20,                  # max chunks to return if many pass threshold
#     },
# )


# def retrieve_chunks(query: str, section_filter: str = None):
#     """
#     Retrieve relevant document chunks for a given query.

#     Args:
#         query:          The lawyer's natural language query.
#         section_filter: Optional. Restrict retrieval to a section type —
#                         'holding', 'facts', 'order', 'reasoning', 'headnote', 'arguments'
#     """

#     if section_filter:
#         # Filtered retrieval using chunk metadata
#         relevant_docs = db.as_retriever(
#             search_type="mmr",
#             search_kwargs={
#                 "k": 5,
#                 "fetch_k": 20,
#                 "lambda_mult": 0.7,
#                 "filter": {"section_type": section_filter},
#             },
#         ).invoke(query)
#     else:
#         relevant_docs = retriever.invoke(query)

#     print(f"User Query: {query}")
#     if section_filter:
#         print(f"Filter: section_type = {section_filter}")
#     print(f"Retrieved {len(relevant_docs)} chunks")

#     print("--- Context ---")
#     for i, doc in enumerate(relevant_docs, 1):
#         m = doc.metadata
#         print(f"\nDocument {i}:")
#         print(f"  Case      : {m.get('appellant', '?')} v. {m.get('respondent', '?')}")
#         print(f"  Citation  : {m.get('citation', '?')}")
#         print(f"  Date      : {m.get('judgment_date', '?')}")
#         print(f"  Outcome   : {m.get('outcome', '?')}")
#         print(f"  Section   : {m.get('section_type', '?')}")
#         print(f"  Page      : {m.get('page', '?')}")
#         print(f"  Content   :\n{doc.page_content}\n")

#     return relevant_docs


from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Must match the model used in vector_store.py exactly
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "legal_cases"

# Cache the embedding model globally so it loads once per server start,
# not on every single query (was causing slow responses + OOM on free tier)
_embedding_model = None

def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        print("Loading embedding model (first query only)…")
        _embedding_model = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embedding_model


def retrieve_chunks(query: str, vector_store_path=None, section_filter=None):
    """
    Retrieve relevant document chunks for a given query.

    Args:
        query:              natural language query
        vector_store_path:  path to ChromaDB for this session
        section_filter:     optional metadata filter e.g. "holding"
    """
    if vector_store_path is None:
        from rag.config import VECTOR_STORE_DIR
        vector_store_path = str(VECTOR_STORE_DIR)

    db = Chroma(
        persist_directory=vector_store_path,
        embedding_function=_get_embedding_model(),
        collection_name=COLLECTION_NAME,
        collection_metadata={"hnsw:space": "cosine"},
    )

    search_kwargs = {"score_threshold": 0.3, "k": 10}

    if section_filter:
        search_kwargs["filter"] = {"section_type": section_filter}

    retriever = db.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs=search_kwargs,
    )

    relevant_docs = retriever.invoke(query)

    print(f"Query: {query}")
    print(f"Retrieved {len(relevant_docs)} chunks from {vector_store_path}")

    return relevant_docs