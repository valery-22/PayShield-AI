"""
Structured logging setup for PayShield AI.
Uses JSON format for easy parsing and analysis.
"""

import logging
import logging.config
import json
import sys
from typing import Dict, Any
from datetime import datetime, timezone

from pythonjsonlogger import jsonlogger

from app.config import settings


class ContextualFilter(logging.Filter):
    """Filter to add contextual information to logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to log record."""
        record.timestamp = datetime.now(timezone.utc).isoformat()
        record.environment = settings.ENV
        record.version = settings.APP_VERSION
        return True


def setup_logging() -> None:
    """Configure logging for the application."""
    
    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": jsonlogger.JsonFormatter,
                "fmt": "%(timestamp)s %(level)s %(name)s %(message)s %(environment)s %(version)s",
            },
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        },
        "filters": {
            "context": {
                "()": ContextualFilter,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL,
                "formatter": settings.LOG_FORMAT,
                "stream": "ext://sys.stdout",
                "filters": ["context"],
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": settings.LOG_LEVEL,
                "formatter": settings.LOG_FORMAT,
                "filename": "logs/payshield.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10,
                "filters": ["context"],
            },
        },
        "loggers": {
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "sqlalchemy": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
            "app": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file"],
                "propagate": False,
            },
        },
        "root": {
            "level": settings.LOG_LEVEL,
            "handlers": ["console", "file"],
        },
    }

    logging.config.dictConfig(logging_config)
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured: {settings.LOG_FORMAT} format, {settings.LOG_LEVEL} level")


def get_logger(name: str) -> logging.Logger:
    """Get logger instance."""
    return logging.getLogger(name)


class LoggerAdapter:
    """Adapter for adding context to logs."""

    def __init__(self, logger: logging.Logger, request_id: str):
        """Initialize adapter."""
        self.logger = logger
        self.request_id = request_id

    def info(self, message: str, **kwargs) -> None:
        """Log info with request context."""
        kwargs["request_id"] = self.request_id
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning with request context."""
        kwargs["request_id"] = self.request_id
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log error with request context."""
        kwargs["request_id"] = self.request_id
        self.logger.error(message, extra=kwargs)

    def debug(self, message: str, **kwargs) -> None:
        """Log debug with request context."""
        kwargs["request_id"] = self.request_id
        self.logger.debug(message, extra=kwargs)