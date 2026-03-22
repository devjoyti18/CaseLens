# ContractChatbot — Legal RAG Chatbot

A Retrieval-Augmented Generation (RAG) chatbot that enables lawyers to query Indian Supreme Court judgment PDFs using natural language and receive precise, cited answers grounded exclusively in the provided case documents.

---

## What It Does

- Upload Indian Supreme Court judgment PDFs as your knowledge base
- Ask natural language questions about case holdings, facts, orders, and directions
- Receive answers that cite the exact case name, citation, and page number
- Every answer is grounded strictly in the documents — no hallucination, no outside knowledge

---

## Tech Stack

| Component | Technology |
|---|---|
| Framework | LangChain |
| Embeddings | BAAI/bge-base-en-v1.5 (HuggingFace) |
| Vector Store | ChromaDB |
| LLM | Groq API — Llama 3.3 70B |
| PDF Parsing | PyPDF |
| Language | Python 3.10+ |

---

## Project Structure

```
ContractChatbot/
├── frontend/                          # UI (upcoming)
├── rag/
│   ├── core/
│   │   ├── chunking/
│   │   │   └── text_splitter.py       # Splits documents into chunks
│   │   ├── embedding/
│   │   │   └── vector_store.py        # Embeds chunks into ChromaDB
│   │   ├── parser/
│   │   │   └── document_loader.py     # Loads PDFs with legal metadata
│   │   ├── retrieval/
│   │   │   ├── similaritySearch.py    # Retrieves relevant chunks
│   │   │   └── responseGenerator.py  # Generates cited answers via LLM
│   │   └── vectorStore/               # ChromaDB persisted here (auto-created)
│   ├── dataStore/
│   │   └── rawData/                   # Place your PDF files here
│   ├── config.py                      # Path configuration
│   └── pipeline.py                    # Orchestrates ingestion + query
├── .env                               # API keys (not committed — create locally)
├── .gitignore
├── main.py                            # Entry point
└── requirements.txt
```

---

## Pipeline Architecture

```
INGESTION                                    QUERY
─────────────────────────────────────────────────────────────────
Raw PDFs                                     Lawyer Question
    │                                              │
    ▼                                              ▼
document_loader.py                         BGE Embeddings
(PyPDF + legal metadata)                   (query prompt)
    │                                              │
    ▼                                              ▼
text_splitter.py                        similaritySearch.py
(800ch chunks, section tags)            (threshold=0.3, k=20)
    │                                              │
    ▼                                         ◄───┘
BGE Embeddings                          ChromaDB lookup
(document prompt)                              │
    │                                          ▼
    ▼                                  responseGenerator.py
ChromaDB ──────────────────────────►  (Groq · Llama 3.3 70B)
(legal_cases collection)                       │
                                               ▼
                                       Cited Legal Answer
```

---

## Local Setup — Step by Step

### Prerequisites

- Python 3.10 or higher — [python.org](https://www.python.org/downloads/)
- Git — [git-scm.com](https://git-scm.com/)
- VS Code — [code.visualstudio.com](https://code.visualstudio.com/)
- A free Groq API key — [console.groq.com](https://console.groq.com)

---

### Step 1 — Clone the Repository

Open VS Code, open the terminal (`Ctrl + `` ` ``), and run:

```bash
git clone https://github.com/AryaRoy2005/LegalChatbotViaRAGModel.git
cd LegalChatbotViaRAGModel
```

---

### Step 2 — Open in VS Code

```bash
code .
```

Or go to **File → Open Folder** and select the cloned folder.

---

### Step 3 — Create a Virtual Environment

In the VS Code terminal:

```bash
# Windows
python -m venv rag/venv

# Mac / Linux
python3 -m venv rag/venv
```

---

### Step 4 — Activate the Virtual Environment

```bash
# Windows (PowerShell)
.\rag\venv\Scripts\Activate.ps1

# Windows (Command Prompt)
.\rag\venv\Scripts\activate.bat

# Mac / Linux
source rag/venv/bin/activate
```

You should see `(venv)` appear at the start of your terminal prompt.

---

### Step 5 — Install Dependencies

```bash
pip install -r requirements.txt
```

This will take a few minutes as it downloads PyTorch and the embedding model dependencies.

---

### Step 6 — Get a Free Groq API Key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up for a free account
3. Click **API Keys** in the left sidebar
4. Click **Create API Key**
5. Copy the key — it starts with `gsk_`

---

### Step 7 — Create Your `.env` File

In the project root (same folder as `main.py`), create a file called `.env`:

```
GROQ_API_KEY=your_groq_api_key_here
```

Replace `your_groq_api_key_here` with the key you copied in Step 6.

> ⚠️ Never share this file or commit it to Git. It is already listed in `.gitignore`.

---

### Step 8 — Add Your PDF Documents

Place your PDF files inside:

```
rag/dataStore/rawData/
```

The system is optimised for Indian Supreme Court judgment PDFs but will work with any legal PDF documents.

---

### Step 9 — Run the Chatbot

```bash
python main.py
```

On first run, the system will:
1. Load and parse all PDFs from `rawData/`
2. Extract legal metadata (citation, parties, judges, outcome)
3. Split documents into chunks
4. Generate embeddings and store in ChromaDB
5. Enter the interactive query loop

You will see:

```
✅ Ingestion complete! Your documents are now ready for RAG queries.

Ask a question (or type 'quit'):
```

---

### Step 10 — Ask Questions

Type your legal query and press Enter:

```
Ask a question (or type 'quit'): What was the Supreme Court's final order?
```

The system will return a cited answer referencing the specific case, citation, and page number.

---

## Example Queries

```
What was the Supreme Court's final order regarding unauthorized construction?

What notices were issued under Section 314 of the MMC Act?

What is the legal position on compounding of building deviations?

What directions were given to the builder regarding regularization?
```

---

## Skipping Ingestion on Subsequent Runs

After the first run, the vector store is saved to disk. To skip re-ingestion and go straight to querying, comment out the ingestion line in `main.py`:

```python
# ingestion_pipeline()   <- comment this out
query_pipeline()
```

Uncomment it again whenever you add new PDF documents.

---

## Metadata Extracted Per Document

The system automatically extracts the following fields from each judgment:

| Field | Description |
|---|---|
| `citation` | SCR citation e.g. [2012] 5 S.C.R. 218 |
| `appellant` | First party name |
| `respondent` | Opposing party name |
| `appeal_number` | Civil appeal number |
| `judges` | Bench composition |
| `judgment_date` | Date of judgment |
| `outcome` | dismissed / allowed / unknown |
| `section_type` | holding / facts / order / reasoning / headnote / arguments |
| `page` | Page number within the PDF |

---

## Hardware Requirements

| Component | Minimum |
|---|---|
| RAM | 4 GB |
| Storage | 2 GB free (for model cache) |
| CPU | Any modern processor |
| GPU | Not required |

> The embedding model (`BAAI/bge-base-en-v1.5`) runs entirely on CPU. No GPU needed.

---

## Troubleshooting

**`GroqError: api_key must be set`**
→ Check your `.env` file exists at the project root and contains `GROQ_API_KEY=your_key`

**`No files found in rawData`**
→ Make sure your PDFs are placed inside `rag/dataStore/rawData/`

**`ModuleNotFoundError`**
→ Make sure your virtual environment is activated and you ran `pip install -r requirements.txt`

**Metadata showing `?` for all retrieved chunks**
→ Ensure `collection_name="legal_cases"` is set in both `vector_store.py` and `similaritySearch.py`

**Chunk count growing on each run (87 → 174 → ...)**
→ The `shutil.rmtree` block in `vector_store.py` clears the old store before rebuilding. Make sure it is present.

---

## Course Details

**Course:** 6th Semester Mini Project — CS37001
**Institution:** KIIT University
**Guide:** Dr. Jagannath Singh

**Team:**
| Roll Number | Name |
|---|---|
| 23051161 | Ali Ahmad |
| 23051331 | Arya Roy |
| 23051340 | Deepro Bhattacharyya |
| 23053505 | Devjoyti Jana |

---

## License

This project was developed as an academic mini project. All rights reserved by the authors.
