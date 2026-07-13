"""
Centralized structured logging framework.
Provides JSON and console logging using Loguru, incorporating request correlation IDs.
"""
import sys
import logging
from loguru import logger
from asgi_correlation_id import correlation_id

from app.core.config import get_settings


def correlation_id_filter(record: dict) -> bool:
    """
    Injects the current ASGI correlation ID into the log record.
    """
    cid = correlation_id.get()
    record["correlation_id"] = cid if cid else "-"
    return True


class InterceptHandler(logging.Handler):
    """
    Intercepts standard Python logging messages and routes them to Loguru.
    This ensures third-party libraries (like FastAPI/Uvicorn) use our formatting.
    """
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            if frame.f_back:
                frame = frame.f_back
                depth += 1
            else:
                break

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging() -> None:
    """
    Configures the global logger based on environment settings.
    Must be called during application startup.
    """
    settings = get_settings()

    # Clear existing loguru handlers
    logger.remove()

    log_level = settings.logging.level.upper()
    log_format_type = settings.logging.format.lower()

    if log_format_type == "json":
        # Structured JSON logging for production/log aggregators
        log_format = "{message}"
        serialize = True
    else:
        # Human-readable console logging for development
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "cid:<magenta>{correlation_id}</magenta> - <level>{message}</level>"
        )
        serialize = False

    # Add the primary handler pointing to stdout
    logger.add(
        sys.stdout,
        level=log_level,
        format=log_format,
        serialize=serialize,
        filter=correlation_id_filter,
        enqueue=True,  # Ensures thread-safe, asynchronous logging
        backtrace=True,
        diagnose=settings.app.environment != "production" # Hide variable values in prod
    )

    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Redirect specific noisy loggers
    for _logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        _logger = logging.getLogger(_logger_name)
        _logger.handlers = [InterceptHandler()]
        # Uvicorn access logs are extremely verbose; we let Loguru handle the level
        _logger.propagate = False

    logger.info("Structured logging initialized.")
