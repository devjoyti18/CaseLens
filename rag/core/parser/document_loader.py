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
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
from typing import List


def load_documents(docs_path: str) -> List:
    print(f"Loading documents from {docs_path}...")

    documents = []

    for pdf in Path(docs_path).rglob("*.pdf"):
        try:
            pages = PyPDFLoader(str(pdf)).load()
            full_text = "\n".join(p.page_content for p in pages)
            legal_meta = _extract_legal_metadata(full_text, str(pdf))
            for page in pages:
                page.metadata.update(legal_meta)
            documents.extend(pages)
            print(f"  Loaded {pdf.name} ({len(pages)} pages)")
        except Exception as e:
            print(f"  Skipping {pdf.name}: {e}")

    for docx in Path(docs_path).rglob("*.docx"):
        try:
            docs = Docx2txtLoader(str(docx)).load()
            full_text = "\n".join(d.page_content for d in docs)
            meta = _extract_legal_metadata(full_text, str(docx))
            for d in docs:
                d.metadata.update(meta)
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
        raise FileNotFoundError(
            f"No files found in {docs_path}. Please upload your documents first."
        )

    print(f"\n✅ Loaded {len(documents)} pages from {docs_path}")
    return documents


def _extract_legal_metadata(text: str, source_path: str) -> dict:
    """
    Extract structured metadata from Indian Supreme Court judgment text.
    All fields fall back to 'Unknown' (never None) so ChromaDB never rejects them.
    """
    filename_stem = Path(source_path).stem

    # ── Citation ──────────────────────────────────────────────────────────────
    m = re.search(r"[\[\(](\d{4})\]\s+\d+\s+S\.C\.R\.?\s*\d*", text)
    citation = m.group(0).strip() if m else None

    # Fallback: build citation from filename if it looks like a year
    if not citation:
        year_m = re.search(r"\d{4}", filename_stem)
        citation = f"({year_m.group(0)}) — {filename_stem}" if year_m else filename_stem

    # ── Year ──────────────────────────────────────────────────────────────────
    year_m = re.search(r"\d{4}", citation)
    year = year_m.group(0) if year_m else "Unknown"

    # ── Party names ───────────────────────────────────────────────────────────
    # Try standard "APPELLANT\nv.\nRESPONDENT" block in first 2000 chars
    m = re.search(
        r"^([A-Z][A-Z\s&\.\(\)]{4,60}?)\s*\n\s*[Vv]\.?\s*\n\s*([A-Z][A-Z\s&\.\(\)]{4,60})",
        text[:2000], re.M
    )
    if m:
        appellant  = m.group(1).strip()
        respondent = m.group(2).strip()
    else:
        # Fallback: parse filename like "Smith_v_Jones_2021"
        fn_m = re.match(r"(.+?)_v_(.+?)(?:_\d{4})?$", filename_stem, re.I)
        if fn_m:
            appellant  = fn_m.group(1).replace("_", " ").title()
            respondent = fn_m.group(2).replace("_", " ").title()
        else:
            appellant  = filename_stem
            respondent = "Unknown"

    # ── Appeal number ─────────────────────────────────────────────────────────
    m = re.search(r"Civil Appeal No\.\s*([\d]+\s*of\s*\d{4})", text[:4000], re.I)
    appeal_number = m.group(1).strip() if m else "Unknown"

    # ── Judges ────────────────────────────────────────────────────────────────
    judges_found = re.findall(r"\[([A-Z][A-Z\s\.,]+(?:CJ|JJ|J)\.?)\]", text[:3000])
    judges = "; ".join(judges_found[:3]) if judges_found else "Unknown"

    # ── Judgment date ─────────────────────────────────────────────────────────
    m = re.search(
        r"(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)"
        r"\s+\d{1,2},?\s+\d{4}",
        text[:3000], re.I
    )
    judgment_date = m.group(0).strip() if m else "Unknown"

    # ── Outcome ───────────────────────────────────────────────────────────────
    tl = text.lower()
    if "appeal dismissed" in tl or "appeal fails" in tl:
        outcome = "dismissed"
    elif "appeal allowed" in tl or "appeal is allowed" in tl:
        outcome = "allowed"
    else:
        outcome = "unknown"

    return {
        "citation":      citation,
        "year":          year,
        "appellant":     appellant,
        "respondent":    respondent,
        "appeal_number": appeal_number,
        "judges":        judges,
        "judgment_date": judgment_date,
        "outcome":       outcome,
    }