"""
app.py — Flask API server for CaseLens Legal RAG
Place this file at the project root (same level as the rag/ folder).

Run with:
    python app.py
"""

import os
import shutil
import threading
import time
import uuid
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ── CORS ───────────────────────────────────────────────────────────────────────
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ── Base sessions root ─────────────────────────────────────────────────────────
# Every user gets their own subfolder: rag/sessions/<session_id>/
SESSIONS_ROOT = Path(__file__).resolve().parent / "rag" / "sessions"
SESSIONS_ROOT.mkdir(parents=True, exist_ok=True)


# ── Per-session helpers ────────────────────────────────────────────────────────

def get_raw_data_dir(session_id: str) -> Path:
    """Return (and create) the rawData folder for this session."""
    d = SESSIONS_ROOT / session_id / "rawData"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_vector_store_dir(session_id: str) -> Path:
    """Return (and create) the vectorStore folder for this session."""
    d = SESSIONS_ROOT / session_id / "vectorStore"
    d.mkdir(parents=True, exist_ok=True)
    return d


def validate_session_id(sid: str) -> bool:
    """Allow only safe UUID-shaped session IDs to prevent path traversal."""
    import re
    return bool(re.fullmatch(r"[a-f0-9\-]{36}", sid))


def get_session_id() -> str | None:
    sid = request.headers.get("X-Session-ID", "").strip()
    if not sid or not validate_session_id(sid):
        return None
    return sid


# ── Per-session ingestion state ────────────────────────────────────────────────
# { session_id: { "running": bool, "done": bool, "error": str|None } }
_ingest_states: dict[str, dict] = {}
_ingest_lock = threading.Lock()


def _get_ingest_state(session_id: str) -> dict:
    with _ingest_lock:
        if session_id not in _ingest_states:
            _ingest_states[session_id] = {"running": False, "done": False, "error": None}
        return dict(_ingest_states[session_id])   # safe copy


def _set_ingest_state(session_id: str, **kwargs):
    with _ingest_lock:
        if session_id not in _ingest_states:
            _ingest_states[session_id] = {"running": False, "done": False, "error": None}
        _ingest_states[session_id].update(kwargs)


# ── Session cleanup daemon ─────────────────────────────────────────────────────
# Runs every hour; deletes session folders older than 2 hours.

def _cleanup_old_sessions():
    while True:
        time.sleep(3600)
        cutoff = time.time() - 7200          # 2 hours
        try:
            for session_dir in SESSIONS_ROOT.iterdir():
                if session_dir.is_dir():
                    try:
                        if session_dir.stat().st_mtime < cutoff:
                            shutil.rmtree(session_dir, ignore_errors=True)
                            with _ingest_lock:
                                _ingest_states.pop(session_dir.name, None)
                            print(f"[cleanup] Removed old session: {session_dir.name}")
                    except Exception:
                        pass
        except Exception:
            pass


threading.Thread(target=_cleanup_old_sessions, daemon=True).start()


# ── Serve frontend ─────────────────────────────────────────────────────────────

@app.route("/")
def serve_index():
    """Serve the main frontend HTML file."""
    return send_from_directory("frontend", "frontend.html")

@app.route("/<path:filename>")
def serve_static(filename):
    """Serve static assets (images, etc.) from project root."""
    return send_from_directory("frontend", filename)


# ── Upload ─────────────────────────────────────────────────────────────────────

@app.route("/api/upload", methods=["POST"])
def upload():
    """
    POST /api/upload
    Header:  X-Session-ID: <uuid>
    Accepts one or more PDF files via multipart/form-data under key 'files'.
    """
    session_id = get_session_id()
    if not session_id:
        return jsonify({"error": "Missing or invalid X-Session-ID header."}), 400

    if "files" not in request.files:
        return jsonify({"error": "No files in request."}), 400

    uploaded = request.files.getlist("files")
    if not uploaded:
        return jsonify({"error": "No files selected."}), 400

    raw_data_dir = get_raw_data_dir(session_id)
    saved, errors = [], []

    for f in uploaded:
        if not f.filename:
            continue
        if not f.filename.lower().endswith(".pdf"):
            errors.append(f"{f.filename} — only PDF files are accepted")
            continue

        safe_name = Path(f.filename).name
        dest = raw_data_dir / safe_name

        try:
            f.save(str(dest))
            saved.append(safe_name)
        except Exception as e:
            errors.append(f"{safe_name} — {str(e)}")

    if not saved and errors:
        return jsonify({"error": errors[0], "all_errors": errors}), 400

    return jsonify({
        "saved":   saved,
        "errors":  errors,
        "total":   len(saved),
        "message": f"{len(saved)} file(s) saved.",
    }), 200


@app.route("/api/documents", methods=["GET"])
def list_documents():
    """GET /api/documents — list PDFs for this session."""
    session_id = get_session_id()
    if not session_id:
        return jsonify({"documents": [], "count": 0}), 200

    raw_data_dir = get_raw_data_dir(session_id)
    pdfs = sorted([f.name for f in raw_data_dir.glob("*.pdf")])
    return jsonify({"documents": pdfs, "count": len(pdfs)}), 200


@app.route("/api/documents/<filename>", methods=["DELETE"])
def delete_document(filename):
    """DELETE /api/documents/<filename> — remove a PDF from this session."""
    session_id = get_session_id()
    if not session_id:
        return jsonify({"error": "Missing or invalid X-Session-ID header."}), 400

    raw_data_dir = get_raw_data_dir(session_id)
    safe_name = Path(filename).name
    target = raw_data_dir / safe_name

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

def _run_ingestion(session_id: str):
    """Background thread: run the ingestion pipeline for one session."""
    try:
        from rag.pipeline import ingestion_pipeline
        raw_data_path = str(get_raw_data_dir(session_id))
        vector_store_path = str(get_vector_store_dir(session_id))
        ingestion_pipeline(raw_data_path=raw_data_path, vector_store_path=vector_store_path)
        _set_ingest_state(session_id, done=True, error=None)
    except Exception as e:
        _set_ingest_state(session_id, error=str(e), done=False)
    finally:
        _set_ingest_state(session_id, running=False)


@app.route("/api/ingest", methods=["POST"])
def ingest():
    session_id = get_session_id()
    if not session_id:
        return jsonify({"error": "Missing or invalid X-Session-ID header."}), 400

    state = _get_ingest_state(session_id)
    if state["running"]:
        return jsonify({"status": "already_running", "message": "Ingestion already in progress."}), 409

    _set_ingest_state(session_id, running=True, done=False, error=None)
    thread = threading.Thread(target=_run_ingestion, args=(session_id,), daemon=True)
    thread.start()

    return jsonify({"status": "started", "message": "Ingestion started in background."}), 202


@app.route("/api/ingest/status", methods=["GET"])
def ingest_status():
    session_id = get_session_id()
    if not session_id:
        return jsonify({"running": False, "done": False, "error": None}), 200
    return jsonify(_get_ingest_state(session_id)), 200


# ── Query ──────────────────────────────────────────────────────────────────────

@app.route("/api/query", methods=["POST"])
def query():
    """
    POST /api/query
    Header:  X-Session-ID: <uuid>
    Body:    { "question": "..." }
    Returns: { "answer": "...", "sources": [...] }
    """
    session_id = get_session_id()
    if not session_id:
        return jsonify({"error": "Missing or invalid X-Session-ID header."}), 400

    data = request.get_json(silent=True)
    if not data or not str(data.get("question", "")).strip():
        return jsonify({"error": "Missing 'question' in request body."}), 400

    question = str(data["question"]).strip()

    vector_store_path = str(get_vector_store_dir(session_id))

    try:
        from rag.core.retrieval.similaritySearch import retrieve_chunks
        from rag.core.retrieval.responseGenerator import generate_answer

        chunks = retrieve_chunks(question, vector_store_path=vector_store_path)
        answer = generate_answer(question, chunks)

        sources = []
        for chunk in chunks:
            meta = getattr(chunk, "metadata", {}) or {}
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
    session_id = get_session_id()
    doc_count = 0
    ingest_state = {"running": False, "done": False, "error": None}

    if session_id:
        raw_data_dir = get_raw_data_dir(session_id)
        doc_count = len(list(raw_data_dir.glob("*.pdf")))
        ingest_state = _get_ingest_state(session_id)

    return jsonify({
        "status":               "ok",
        "documents_in_rawData": doc_count,
        "ingestion":            ingest_state,
    }), 200


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)