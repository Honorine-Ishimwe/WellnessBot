"""
Structured JSON logging for WellnessBot.
"""

import logging
import json
import sys
import uuid
from datetime import datetime, timezone

from flask import request, g


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for structured logging."""

    def format(self, record):
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }

        # Include request ID if available
        if hasattr(g, "request_id"):
            log_data["request_id"] = g.request_id

        # Include exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_data["exception"] = self.formatException(record.exc_info)

        # Include any extra fields
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


def setup_logger(name="wellnessbot"):
    """Create and configure the application logger."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers on re-init
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

    return logger


# Singleton logger instance
logger = setup_logger()


def request_logging_middleware(app):
    """Register before/after request hooks for logging."""

    @app.before_request
    def before_request():
        g.request_id = str(uuid.uuid4())[:8]
        g.request_start = datetime.now(timezone.utc)

    @app.after_request
    def after_request(response):
        # Don't log health checks to reduce noise
        if request.path == "/health":
            return response

        duration_ms = 0
        if hasattr(g, "request_start"):
            delta = datetime.now(timezone.utc) - g.request_start
            duration_ms = round(delta.total_seconds() * 1000)

        logger.info(
            f"{request.method} {request.path} → {response.status_code}",
            extra={
                "extra_data": {
                    "method": request.method,
                    "path": request.path,
                    "status": response.status_code,
                    "duration_ms": duration_ms,
                }
            },
        )
        return response
