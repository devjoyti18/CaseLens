# ContractChatbot — Legal RAG System

A full-stack Retrieval-Augmented Generation (RAG) application designed to query Indian Supreme Court case documents using natural language.

---
## 💡 Why this project?

Legal documents are complex and difficult to search manually.  
This project uses Retrieval-Augmented Generation (RAG) to enable precise, citation-backed answers from legal case documents.

---

## 🚀 Features

* Upload PDF legal documents
* Automatic document parsing and chunking
* Vector embeddings using transformer models
* Semantic search using ChromaDB
* AI-generated answers grounded in source documents
* Source citation for every answer
* Clean frontend UI with chat interface

---

## 🏗️ Tech Stack

### Backend

* Python
* Flask API
* LangChain
* ChromaDB
* HuggingFace / Ollama / Groq

### Frontend

* HTML, CSS, JavaScript
* Custom chat UI

---

## 📁 Project Structure

```
project-root/
│
├── app.py                # Flask API server
├── main.py               # (Optional CLI runner)
├── requirements.txt
├── config.py
│
├── rag/
│   ├── core/
│   ├── dataStore/
│   │   ├── rawData/
│   │   └── vectorStore/
│   └── pipeline.py
│
└── frontend.html
```

---

## ⚙️ Setup Instructions

### 1. Clone repository

```
git clone https://github.com/your-username/contract-chatbot.git
cd contract-chatbot
```

### 2. Create virtual environment

```
python -m venv venv
source venv/bin/activate   # mac/linux
venv\Scripts\activate      # windows
```

### 3. Install dependencies

```
pip install -r requirements.txt
```

### 4. Add environment variables

Create a `.env` file:

```
GROQ_API_KEY=your_key
```

---

## ▶️ Running the Project

### Start backend

```
python app.py
```

### Open frontend

Just open:

```
frontend.html
```

---

## 🔄 Workflow

1. Upload PDF documents
2. Click **Build Index**
3. Ask questions
4. Get AI answers with citations

---

## 📌 API Endpoints

* `POST /api/upload` → Upload PDFs
* `GET /api/documents` → List documents
* `POST /api/ingest` → Build vector index
* `GET /api/ingest/status` → Check ingestion
* `POST /api/query` → Ask questions
* `GET /api/health` → Server health

---

## ⚠️ Limitations

* Only PDF files supported
* Requires manual ingestion step
* Performance depends on embedding model

---

## 🔮 Future Improvements

* Authentication system
* Cloud deployment
* Streaming responses
* Multi-user sessions
* Better legal summarization
