"""
app.domain.exceptions
---------------------
Re-exports core exceptions under the domain namespace so that domain-layer
and application-layer code can import from here without depending on
app.core directly.
"""
from app.core.exceptions import (
    CaptionDBException,
    ValidationException,
    NotFoundException,
    ConflictException,
)

# Canonical alias used throughout auth and application services.
DomainException = CaptionDBException

__all__ = [
    "DomainException",
    "CaptionDBException",
    "ValidationException",
    "NotFoundException",
    "ConflictException",
]
