# import os

# from dotenv import load_dotenv
# from langchain_core.documents import Document

# from rag.core.parser.document_loader import load_documents
# from rag.core.chunking.text_splitter import split_documents
# from rag.core.embedding.vector_store import create_vector_store
# from rag.core.retrieval.similaritySearch import retrieve_chunks
# from rag.core.retrieval.responseGenerator import generate_answer
# from rag.config import VECTOR_STORE_DIR


# # Load environment variables from .env file
# load_dotenv()


# # Ingestion Pipeline

# def ingestion_pipeline():


#     # 1. Load raw data from rawData
#     base_dir = os.path.dirname(__file__)
#     raw_data_path = os.path.join(base_dir, "dataStore", "rawData")
#     parsed_data_path = os.path.join(base_dir, "dataStore", "parsedData")
#     vectorstore_dir = VECTOR_STORE_DIR


#     # 2. Parse raw data and store in parsedData
#     documents = load_documents(raw_data_path)

#     parsed_files = []

#     for i, doc in enumerate(documents):
#         parsed_file = os.path.join(parsed_data_path, f"parsed_{i+1}.txt")
#         with open(parsed_file, "w", encoding="utf-8") as f:
#             f.write(doc.page_content)
#         parsed_files.append(parsed_file)

#     print(f"Parsed {len(parsed_files)} files and saved to {parsed_data_path}")


#     # 3. Feed parsed data into chunking
#     parsed_documents = []

#     for file in parsed_files:
#         with open(file, "r", encoding="utf-8") as f:
#             content = f.read()
#         # Simulate Document object as in langchain
#         parsed_documents.append(Document(page_content=content, metadata={"source": file}))

#     chunks = split_documents(parsed_documents)


#     # 4. Embed chunks and store vectorstore
#     create_vector_store(chunks)
#     print("\n✅ Ingestion complete! Your documents are now ready for RAG queries.")




# # Query Response Pipeline
# def query_pipeline():

#     while True:
#         query = input("\nAsk a question (or type 'quit'): ").strip()
#         if query.lower() == "quit":
#             break

#         chunks = retrieve_chunks(query)
#         answer = generate_answer(query, chunks)

#         print("\nAnswer:\n", answer)














import os

from dotenv import load_dotenv

from rag.core.parser.document_loader import load_documents
from rag.core.chunking.text_splitter import split_documents
from rag.core.embedding.vector_store import create_vector_store
from rag.core.retrieval.similaritySearch import retrieve_chunks
from rag.core.retrieval.responseGenerator import generate_answer
from rag.config import VECTOR_STORE_DIR


# Load environment variables from .env file
load_dotenv()


# Ingestion Pipeline
def ingestion_pipeline():

    base_dir = os.path.dirname(__file__)
    raw_data_path = os.path.join(base_dir, "dataStore", "rawData")

    # 1. Load raw documents with full legal metadata
    documents = load_documents(raw_data_path)

    # 2. Feed directly into chunking — metadata stays intact
    chunks = split_documents(documents)

    # 3. Embed chunks and store in vector store
    create_vector_store(chunks)

    print("\n✅ Ingestion complete! Your documents are now ready for RAG queries.")


# Query Response Pipeline
def query_pipeline():

    while True:
        query = input("\nAsk a question (or type 'quit'): ").strip()
        if query.lower() == "quit":
            break

        chunks = retrieve_chunks(query)
        answer = generate_answer(query, chunks)

        print("\nAnswer:\n", answer)