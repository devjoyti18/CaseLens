# import os

# from langchain_community.document_loaders import TextLoader, DirectoryLoader, PyPDFLoader,Docx2txtLoader


# def load_documents(docs_path):

#     #Load all text files from the given directory (rawData)
#     print(f"Loading documents from {docs_path}...")


#     # Initialize loaders for different file types
#     loaders = [
#         DirectoryLoader(path=docs_path, glob="**/*.txt", loader_cls=TextLoader),
#         DirectoryLoader(path=docs_path, glob="**/*.pdf", loader_cls=PyPDFLoader),
#         DirectoryLoader(path=docs_path, glob="**/*.docx", loader_cls=Docx2txtLoader),
#     ]


#     # Load documents using all loaders
#     documents = []
#     for loader in loaders:
#         documents.extend(loader.load())

#     if len(documents) == 0:
#         raise FileNotFoundError(f"No files found in {docs_path}. Please add your company documents.")
    

#     # Display loaded documents info
#     for i, doc in enumerate(documents[:2]):
#         print(f"\nDocument {i+1}:")
#         print(f"  Source: {doc.metadata['source']}")
#         print(f"  Content length: {len(doc.page_content)} characters")
#         print(f"  Content preview: {doc.page_content[:100]}...")
#         print(f"  metadata: {doc.metadata}")


#     return documents





































import os
import re
from pathlib import Path
from langchain_community.document_loaders import TextLoader, DirectoryLoader, PyPDFLoader, Docx2txtLoader
# from langchain.schema import Document
from typing import List


# def load_documents(docs_path: str) -> List[Document]:
def load_documents(docs_path: str) -> List:
    print(f"Loading documents from {docs_path}...")

    documents = []

    # Load per-file so page numbers are preserved in metadata
    for pdf in Path(docs_path).rglob("*.pdf"):
        try:
            pages = PyPDFLoader(str(pdf)).load()

            # Extract legal metadata from full text (stitched pages)
            full_text = "\n".join(p.page_content for p in pages)
            legal_meta = _extract_legal_metadata(full_text, str(pdf))

            for page in pages:
                page.metadata.update(legal_meta)

            documents.extend(pages)
        except Exception as e:
            print(f"  Skipping {pdf.name}: {e}")

    for docx in Path(docs_path).rglob("*.docx"):
        try:
            docs = Docx2txtLoader(str(docx)).load()
            full_text = "\n".join(d.page_content for d in docs)
            for d in docs:
                d.metadata.update(_extract_legal_metadata(full_text, str(docx)))
            documents.extend(docs)
        except Exception as e:
            print(f"  Skipping {docx.name}: {e}")

    for txt in Path(docs_path).rglob("*.txt"):
        try:
            docs = TextLoader(str(txt), encoding="utf-8").load()
            for d in docs:
                d.metadata.update(_extract_legal_metadata(d.page_content, str(txt)))
            documents.extend(docs)
        except Exception as e:
            print(f"  Skipping {txt.name}: {e}")

    if not documents:
        raise FileNotFoundError(f"No files found in {docs_path}. Please add your documents.")

    # Display loaded documents info
    for i, doc in enumerate(documents[:2]):
        print(f"\nDocument {i+1}:")
        print(f"  Source: {doc.metadata['source']}")
        print(f"  Content length: {len(doc.page_content)} characters")
        print(f"  Content preview: {doc.page_content[:100]}...")
        print(f"  Metadata: {doc.metadata}")

    return documents


def _extract_legal_metadata(text: str, source_path: str) -> dict:
    """Extract structured metadata from Indian Supreme Court judgment text."""
    meta = {}

    # Citation — tolerates OCR artifact '(' instead of '['
    m = re.search(r"[\[\(](\d{4})\]\s+\d+\s+S\.C\.R\.?\s+\d+", text)
    meta["citation"] = m.group(0).strip() if m else None

    # Year — fall back to filename
    meta["year"] = m.group(1) if m else (re.search(r"\d{4}", Path(source_path).stem) or [None])[0]

    # Party names
    m = re.search(r"^([A-Z][A-Z\s&\.]{5,}?)\s*\n\s*v\.?\s*\n\s*([A-Z][A-Z\s&\.]{5,})", text[:2000], re.M)
    meta["appellant"]  = m.group(1).strip() if m else None
    meta["respondent"] = m.group(2).strip() if m else None

    # Appeal number
    m = re.search(r"Civil Appeal No\.\s*([\d]+\s*of\s*\d{4})", text[:4000], re.I)
    meta["appeal_number"] = m.group(1).strip() if m else None

    # Judges
    judges = re.findall(r"\[([A-Z][A-Z\s\.,]+(?:CJ|JJ|J)\.?)\]", text[:3000])
    meta["judges"] = "; ".join(judges[:3]) if judges else None

    # Judgment date
    m = re.search(r"(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+\d{1,2},?\s+\d{4}", text[:3000], re.I)
    meta["judgment_date"] = m.group(0).strip() if m else None

    # Outcome
    tl = text.lower()
    if "appeal dismissed" in tl or "appeal fails" in tl:
        meta["outcome"] = "dismissed"
    elif "appeal allowed" in tl or "appeal is allowed" in tl:
        meta["outcome"] = "allowed"
    else:
        meta["outcome"] = "unknown"

    return meta