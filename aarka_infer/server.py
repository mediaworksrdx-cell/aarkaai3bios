"""
AARKA Infer Standalone Serving Application
FastAPI server entry point with CORS, graceful shutdown, and CLI launcher.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aarka_infer.api.routes import router
from aarka_infer.config import settings
from aarka_infer.runtime.engine import AarkaInferEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("aarka_infer.server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager: initializes the inference engine at startup."""
    logger.info("Initializing AARKA Infer engine on startup...")
    engine = AarkaInferEngine.get_instance()
    await engine.initialize()
    yield
    logger.info("AARKA Infer shutting down gracefully...")


def create_app() -> FastAPI:
    """Builds and configures the FastAPI application."""
    app = FastAPI(
        title="AARKA Infer Serving Engine",
        description="Dedicated, High-Performance Inference Subsystem for AARKAA-3B",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Enable CORS for web terminal & client applications
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    return app


app = create_app()


def main():
    """CLI runner for standalone deployment."""
    parser = argparse.ArgumentParser(description="AARKA Infer: High-Performance Serving for AARKAA-3B")
    parser.add_argument("--host", default=settings.host, help="Server host IP")
    parser.add_argument("--port", type=int, default=settings.port, help="Server port (default: 8008)")
    parser.add_argument("--backend", default=settings.backend, help="Backend: auto | llama_cpp | vllm | mock")
    parser.add_argument("--reload", action="store_true", help="Enable hot reload")
    args = parser.parse_args()

    settings.host = args.host
    settings.port = args.port
    if args.backend:
        settings.backend = args.backend

    logger.info("Starting AARKA Infer on http://%s:%d (backend: %s)", args.host, args.port, settings.backend)
    uvicorn.run("aarka_infer.server:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
