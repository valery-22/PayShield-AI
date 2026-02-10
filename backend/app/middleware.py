"""
Custom middleware for PayShield AI.
Handles CORS, request tracking, error handling.
"""

import time
import uuid
import logging
from typing import Callable
from datetime import datetime, timezone

from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.config import settings
from app.constants import REQUEST_ID_HEADER, CORRELATION_ID_HEADER

logger = logging.getLogger(__name__)


def add_cors_middleware(app: ASGIApp) -> None:
    """Add CORS middleware to app."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_CREDENTIALS,
        allow_methods=settings.CORS_METHODS,
        allow_headers=settings.CORS_HEADERS,
    )


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID and correlation ID to requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add request tracking IDs."""
        # Generate or use existing request ID
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        correlation_id = request.headers.get(CORRELATION_ID_HEADER) or str(uuid.uuid4())

        # Store in request state
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id
        request.state.start_time = time.time()

        # Call next middleware/endpoint
        response = await call_next(request)

        # Add headers to response
        response.headers[REQUEST_ID_HEADER] = request_id
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        response.headers["X-Process-Time"] = str(time.time() - request.state.start_time)

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request details."""
        start_time = time.time()

        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_string": str(request.url.query),
                "request_id": getattr(request.state, "request_id", "unknown"),
            },
        )

        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "error": str(e),
                    "request_id": getattr(request.state, "request_id", "unknown"),
                },
                exc_info=True,
            )
            raise

        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Response: {request.method} {request.url.path} {response.status_code}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": process_time,
                "request_id": getattr(request.state, "request_id", "unknown"),
            },
        )

        return response