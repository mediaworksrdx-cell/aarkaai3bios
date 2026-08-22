"""
AARKAAI Backend – Structured Logging Configuration

Configures JSON-structured logging for production observability.
Uses structlog if available, falls back to stdlib logging.
"""
from __future__ import annotations

import logging
import sys
from typing import Optional


def configure_logging(
    log_level: str = "INFO",
    json_format: bool = True,
    service_name: str = "aarkaai",
) -> None:
    """Configure application-wide logging.
    
    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        json_format: If True, output JSON-structured logs (for production).
        service_name: Service identifier included in each log line.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    try:
        import structlog
        
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
        ]
        
        if json_format:
            processors.append(structlog.processors.JSONRenderer())
        else:
            processors.append(structlog.dev.ConsoleRenderer())
        
        structlog.configure(
            processors=processors,
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        # Configure stdlib logging to route through structlog
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=level,
        )
        
        logger = structlog.get_logger()
        logger.info("Structured logging configured", service=service_name, level=log_level)
        
    except ImportError:
        # Fallback: stdlib JSON-ish logging
        fmt = (
            '{"time":"%(asctime)s","level":"%(levelname)s",'
            '"logger":"%(name)s","message":"%(message)s"}'
            if json_format
            else "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        
        logging.basicConfig(
            format=fmt,
            datefmt="%Y-%m-%dT%H:%M:%S",
            stream=sys.stdout,
            level=level,
        )
        
        logging.getLogger().info(
            "Logging configured (structlog not available, using stdlib fallback)"
        )


def get_logger(name: Optional[str] = None):
    """Get a logger instance. Uses structlog if available."""
    try:
        import structlog
        return structlog.get_logger(name)
    except ImportError:
        return logging.getLogger(name)
