"""
FastAPI application entry point.
Registers all routes and configures logging.
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.agent.orchestrator import orchestrator
from app.clients.ollama_client import ollama_client
from app.core.schemas import ChatRequest, ChatResponse
from app.core.settings import settings

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown hooks)
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Banking AI-Agent starting up...")
    healthy = await ollama_client.health_check()
    if healthy:
        logger.info("✅ Ollama is reachable at %s (model: %s)", settings.ollama_base_url, settings.model_name)
    else:
        logger.warning(
            "⚠️  Ollama is NOT reachable at %s — draft node will use fallback responses.",
            settings.ollama_base_url,
        )
    yield
    logger.info("Banking AI-Agent shutting down.")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="An AI-powered banking customer support agent with a structured workflow.",
    lifespan=lifespan,
)

# CORS — allow all origins for local demo; tighten in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request timing middleware
# ---------------------------------------------------------------------------


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time-Ms"] = f"{elapsed:.1f}"
    return response


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/", tags=["Health"])
async def root():
    """Root health-check endpoint."""
    return {
        "service": settings.api_title,
        "version": settings.api_version,
        "status": "running",
        "ollama_url": settings.ollama_base_url,
        "model": settings.model_name,
    }


@app.get("/health", tags=["Health"])
async def health():
    """Detailed health check including Ollama connectivity."""
    ollama_ok = await ollama_client.health_check()
    return {
        "status": "healthy" if ollama_ok else "degraded",
        "ollama": "connected" if ollama_ok else "unreachable",
        "model": settings.model_name,
    }


@app.post("/agent/chat", response_model=ChatResponse, tags=["Agent"])
async def chat(request: ChatRequest) -> ChatResponse:
    """Main chat endpoint.

    Processes the customer message through the full AI-Agent workflow
    and returns a structured response with workflow trace.
    """
    logger.info("POST /agent/chat message_len=%d", len(request.message))
    try:
        return await orchestrator.run(request)
    except Exception as exc:
        logger.error("Unhandled error in /agent/chat: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
