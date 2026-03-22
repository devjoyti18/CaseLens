# from langchain_text_splitters import CharacterTextSplitter

# def split_documents(documents, chunk_size=800, chunk_overlap=0):

#     #Split documents into smaller chunks with overlap
#     print("Splitting documents into chunks...")


#     text_splitter = CharacterTextSplitter(
#         chunk_size=chunk_size, 
#         chunk_overlap=chunk_overlap
#     )


#     chunks = text_splitter.split_documents(documents)


#     if chunks:     
#         for i, chunk in enumerate(chunks[:5]):
#             print(f"\n--- Chunk {i+1} ---")
#             print(f"Source: {chunk.metadata['source']}")
#             print(f"Length: {len(chunk.page_content)} characters")
#             print(f"Content:")
#             print(chunk.page_content)
#             print("-" * 50)
#         if len(chunks) > 5:
#             print(f"\n... and {len(chunks) - 5} more chunks")


#     return chunks





























from langchain_text_splitters import RecursiveCharacterTextSplitter
import re

def split_documents(documents, chunk_size=800, chunk_overlap=150):

    print("Splitting documents into chunks...")

    # Clean margin markers from scanned court reports before chunking
    for doc in documents:
        doc.page_content = re.sub(r'\n[A-H]\n', '\n', doc.page_content)
        doc.page_content = re.sub(r' [A-H]\n', '\n', doc.page_content)
        doc.page_content = re.sub(r'\n{3,}', '\n\n', doc.page_content)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", ", ", " "],
    )

    chunks = text_splitter.split_documents(documents)

    # Add chunk index and section type to metadata
    source_counters = {}
    for chunk in chunks:
        source = chunk.metadata.get("source", "unknown")
        source_counters.setdefault(source, 0)
        chunk.metadata["chunk_index"] = source_counters[source]
        chunk.metadata["section_type"] = _detect_section_type(chunk.page_content)
        source_counters[source] += 1

    if chunks:
        for i, chunk in enumerate(chunks[:5]):
            print(f"\n--- Chunk {i+1} ---")
            print(f"Source: {chunk.metadata['source']}")
            print(f"Length: {len(chunk.page_content)} characters")
            print(f"Section type: {chunk.metadata['section_type']}")
            print(f"Content:")
            print(chunk.page_content)
            print("-" * 50)
        if len(chunks) > 5:
            print(f"\n... and {len(chunks) - 5} more chunks")

    return chunks


def _detect_section_type(text: str) -> str:
    tl = text.lower()
    if any(k in tl for k in ["held:", "held :", "it is held"]):
        return "holding"
    if any(k in tl for k in ["brief facts", "background facts"]):
        return "facts"
    if any(k in tl for k in ["we direct", "appeal is dismissed", "appeal dismissed",
                               "appeal is allowed", "appeal allowed"]):
        return "order"
    if any(k in tl for k in ["s.c.r.", "(20", "[20"]):
        return "headnote"
    if any(k in tl for k in ["counsel submitted", "counsel urged", "contention"]):
        return "arguments"
    return "reasoning"