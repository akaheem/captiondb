"""
Core Application Dependencies.
"""
import logging
from loguru import logger
from typing import Generator

def get_logger() -> logging.Logger:
    """
    Dependency provider for the application logger.
    Returns the loguru logger wrapper.
    In future phases, can return contextual loggers bounded with request IDs.
    """
    return logger
