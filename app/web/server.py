"""FastAPI Web Server for Marathi RAG Tutor.

Provides REST API endpoints and serves the modern Web UI.
Run with: python -m app.web.server
"""

import sys
import webbrowser
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

from app.chains.rag_chain import QueryResult
from app.config.constants import APP_NAME, APP_VERSION
from app.config.settings import get_settings
from app.services.query_service import QueryService
from app.utils.logger import get_logger

# Ensure UTF-8 output streams on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logger = get_logger(__name__)

# Directory paths
WEB_DIR = Path(__file__).resolve().parent
STATIC_DIR = WEB_DIR / "static"

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="A textbook-grounded educational RAG system for Maharashtra State Board Marathi (Std. 6).",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global QueryService instance
query_service: Optional[QueryService] = None


class AskRequest(BaseModel):
    """Request schema for asking a question."""
    question: str = Field(..., description="User question in Marathi or English")
    standard: Optional[Any] = Field(default="all", description="Selected standard (6, 7, 8, 9, 10 or 'all')")
    filters: Optional[dict[str, Any]] = Field(default=None, description="Optional retrieval filters")


class ChunkResponse(BaseModel):
    """Retrieved chunk details for the frontend."""
    content: str
    page_number: int
    chapter: str
    chunk_id: str
    score: float


class AskResponse(BaseModel):
    """Response schema for question answering."""
    question: str
    marathi_question: Optional[str] = None
    answer: str
    page_numbers: list[int]
    source: str
    retrieved_chunks: list[ChunkResponse]


@app.on_event("startup")
def startup_event():
    """Initialize QueryService singleton at application startup."""
    global query_service
    logger.info("Initializing Marathi RAG QueryService for Web UI...")
    try:
        query_service = QueryService()
        query_service.initialize()
        logger.info("✅ QueryService ready for incoming queries")
    except Exception as exc:
        logger.error("Failed to initialize QueryService: %s", exc)
        raise exc


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy" if query_service and query_service.is_initialized else "initializing",
        "app_name": APP_NAME,
        "version": APP_VERSION,
    }


@app.get("/api/standards")
def get_standards():
    """Get list of supported standards with indexing status."""
    if not query_service or not query_service.is_initialized:
        from app.config.constants import AVAILABLE_STANDARDS
        return [
            {"standard": k, "name": v["name"], "title": v["title"], "chunk_count": 0, "is_indexed": False}
            for k, v in AVAILABLE_STANDARDS.items()
        ]
    return query_service.get_standards_info()


@app.post("/api/ask", response_model=AskResponse)
def ask_question(req: AskRequest):
    """Ask a textbook question and receive a grounded Marathi response."""
    if not query_service or not query_service.is_initialized:
        raise HTTPException(status_code=503, detail="Query service is still initializing. Please retry in a moment.")

    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        res: QueryResult = query_service.ask(
            question=req.question,
            standard=req.standard,
            filters=req.filters,
        )
        
        chunks = [
            ChunkResponse(
                content=c.content,
                page_number=c.page_number,
                chapter=c.chapter,
                chunk_id=c.chunk_id,
                score=round(c.score, 4),
            )
            for c in res.retrieved_chunks
        ]

        return AskResponse(
            question=res.question,
            marathi_question=res.marathi_question,
            answer=res.answer,
            page_numbers=res.page_numbers,
            source=res.source,
            retrieved_chunks=chunks,
        )
    except Exception as exc:
        logger.error("Error answering question '%s': %s", req.question, exc)
        raise HTTPException(status_code=500, detail=str(exc))


# Serve static frontend files
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def serve_index():
    """Serve the single-page application UI."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse(
        content={"message": "Marathi RAG API is running. UI files not found in static directory."},
        status_code=200,
    )


def main():
    """CLI launcher for the Web server."""
    port = 8000
    host = "127.0.0.1"
    url = f"http://{host}:{port}"
    print(f"\n🌐 Starting Marathi RAG Web Tutor at {url}")
    print("✨ Opening your default browser...\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    uvicorn.run("app.web.server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
