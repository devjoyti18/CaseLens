"""
app.py — Flask API server for ContractChatbot
Place this file at the project root (same level as main.py)

Run with:
    python app.py
"""

import os
import threading
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Path where uploaded PDFs are saved (same folder the RAG pipeline reads from)
RAW_DATA_DIR = Path(__file__).resolve().parent / "rag" / "dataStore" / "rawData"
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Track ingestion state
ingestion_status = {
    "running": False,
    "done":    False,
    "error":   None,
}


# ── Upload ─────────────────────────────────────────────────────────────────────

@app.route("/api/upload", methods=["POST"])
def upload():
    """
    POST /api/upload
    Accepts one or more PDF files via multipart/form-data under the key 'files'.
    Saves them to rag/dataStore/rawData/.
    """
    if "files" not in request.files:
        return jsonify({"error": "No files in request."}), 400

    uploaded = request.files.getlist("files")
    if not uploaded:
        return jsonify({"error": "No files selected."}), 400

    saved, errors = [], []

    for f in uploaded:
        if not f.filename:
            continue
        if not f.filename.lower().endswith(".pdf"):
            errors.append(f"{f.filename} — only PDF files are accepted")
            continue

        safe_name = Path(f.filename).name          # strip any path separators
        dest = RAW_DATA_DIR / safe_name

        try:
            f.save(dest)
            saved.append(safe_name)
        except Exception as e:
            errors.append(f"{safe_name} — {str(e)}")

    if not saved and errors:
        return jsonify({"error": errors[0], "all_errors": errors}), 400

    return jsonify({
        "saved":   saved,
        "errors":  errors,
        "total":   len(saved),
        "message": f"{len(saved)} file(s) saved to rawData/."
    }), 200


@app.route("/api/documents", methods=["GET"])
def list_documents():
    """GET /api/documents — list PDFs currently in rawData/."""
    pdfs = sorted([f.name for f in RAW_DATA_DIR.glob("*.pdf")])
    return jsonify({"documents": pdfs, "count": len(pdfs)}), 200


@app.route("/api/documents/<filename>", methods=["DELETE"])
def delete_document(filename):
    """DELETE /api/documents/<filename> — remove a PDF from rawData/."""
    safe_name = Path(filename).name
    target = RAW_DATA_DIR / safe_name

    if not target.exists():
        return jsonify({"error": "File not found."}), 404
    if not safe_name.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files can be deleted here."}), 400

    try:
        target.unlink()
        return jsonify({"deleted": safe_name}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Ingestion ──────────────────────────────────────────────────────────────────

def _run_ingestion():
    global ingestion_status
    try:
        from rag.pipeline import ingestion_pipeline
        ingestion_pipeline()
        ingestion_status["done"]  = True
        ingestion_status["error"] = None
    except Exception as e:
        ingestion_status["error"] = str(e)
    finally:
        ingestion_status["running"] = False


@app.route("/api/ingest", methods=["POST"])
def ingest():
    global ingestion_status

    if ingestion_status["running"]:
        return jsonify({"status": "already_running",
                        "message": "Ingestion already in progress."}), 409

    ingestion_status.update({"running": True, "done": False, "error": None})
    threading.Thread(target=_run_ingestion, daemon=True).start()
    return jsonify({"status": "started",
                    "message": "Ingestion started in background."}), 202


@app.route("/api/ingest/status", methods=["GET"])
def ingest_status():
    return jsonify(ingestion_status), 200


# ── Query ──────────────────────────────────────────────────────────────────────

@app.route("/api/query", methods=["POST"])
def query():
    """
    POST /api/query
    Body:    { "question": "..." }
    Returns: { "answer": "...", "sources": [...] }
    """
    data = request.get_json()
    if not data or not data.get("question", "").strip():
        return jsonify({"error": "Missing 'question' in request body."}), 400

    question = data["question"].strip()

    try:
        from rag.core.retrieval.similaritySearch import retrieve_chunks
        from rag.core.retrieval.responseGenerator import generate_answer

        chunks = retrieve_chunks(question)
        answer = generate_answer(question, chunks)

        sources = []
        for chunk in chunks:
            meta = getattr(chunk, "metadata", {})
            entry = {
                "citation":     meta.get("citation",     "Unknown"),
                "appellant":    meta.get("appellant",    "?"),
                "respondent":   meta.get("respondent",   "?"),
                "page":         meta.get("page",         "?"),
                "section_type": meta.get("section_type", "?"),
                "outcome":      meta.get("outcome",      "?"),
            }
            if entry not in sources:
                sources.append(entry)

        return jsonify({"answer": answer, "sources": sources}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Health ─────────────────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    count = len(list(RAW_DATA_DIR.glob("*.pdf")))
    return jsonify({"status": "ok", "documents_in_rawData": count}), 200


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)