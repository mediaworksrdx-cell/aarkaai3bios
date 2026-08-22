"""
AARKAAI Backend – Standardized Error Response Handling

Provides unified error response format across all API endpoints.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    """Standardized API error response schema."""
    error_code: str
    message: str
    request_id: Optional[str] = None
    details: Optional[dict] = None


from fastapi.encoders import jsonable_encoder

async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors with structured format."""
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        safe_errors = jsonable_encoder(exc.errors())
    except Exception:
        safe_errors = [str(err) for err in exc.errors()]
        
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            request_id=request_id,
            details={"errors": safe_errors},
        ).model_dump(),
    )


async def http_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle HTTPException with structured format."""
    request_id = getattr(request.state, "request_id", "unknown")
    status_code = getattr(exc, "status_code", 500)
    detail = getattr(exc, "detail", "An error occurred")
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error_code=f"HTTP_{status_code}",
            message=str(detail),
            request_id=request_id,
        ).model_dump(),
    )


async def generic_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle unexpected exceptions with structured format."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        "Unhandled exception [%s] %s %s: %s",
        request_id,
        request.method,
        request.url.path,
        exc,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error_code="INTERNAL_ERROR",
            message="An internal error occurred",
            request_id=request_id,
        ).model_dump(),
    )
