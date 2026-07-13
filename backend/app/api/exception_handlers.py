"""
Global FastAPI exception handlers.
Transforms internal domain exceptions into secure, standardized HTTP responses.
"""
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger
from asgi_correlation_id import correlation_id

from app.core.exceptions import (
    CaptionDBException,
    ValidationException,
    NotFoundException,
    ConflictException,
    StorageException,
    AIProviderException,
    PipelineException,
    ExternalServiceException,
    ConfigurationException,
    AuthenticationException,
    AccountNotActiveException,
    TokenExpiredException,
)
from app.schemas.errors import ErrorResponse


def setup_exception_handlers(app: FastAPI) -> None:
    """Registers all global exception handlers to the FastAPI app."""

    def _build_response(status_code: int, error_code: str, message: str, details: Optional[Dict[str, Any]] = None) -> JSONResponse:
        cid = correlation_id.get()
        
        # In a real environment, you might scrub 'details' here if the environment is production 
        # to ensure absolutley no leak of parameters, but we rely on Domain Exceptions being safe.
        
        response_model = ErrorResponse(
            error_code=error_code,
            message=message,
            correlation_id=cid,
            details=details
        )
        return JSONResponse(status_code=status_code, content=response_model.model_dump(mode="json"))

    @app.exception_handler(CaptionDBException)
    async def captiondb_exception_handler(request: Request, exc: CaptionDBException) -> JSONResponse:
        """
        Catches all custom domain exceptions.
        Maps specific domain exceptions to correct HTTP status codes.
        """
        logger.error(f"Domain Error [{exc.error_code}]: {exc.message} | Details: {exc.details}")
        
        status_code = 500
        if isinstance(exc, ValidationException):
            status_code = 400
        elif isinstance(exc, AccountNotActiveException):
            status_code = 403
        elif isinstance(exc, (TokenExpiredException, AuthenticationException)):
            status_code = 401
        elif isinstance(exc, NotFoundException):
            status_code = 404
        elif isinstance(exc, ConflictException):
            status_code = 409

        # Scrub 500-level errors to prevent leaking implementation details (SQLAlchemy/Fireworks)
        safe_message = exc.message
        safe_details = exc.details
        if status_code >= 500:
            safe_message = "An internal server error occurred."
            safe_details = None

        return _build_response(
            status_code=status_code,
            error_code=exc.error_code,
            message=safe_message,
            details=safe_details
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """
        Catches FastAPI's built-in validation errors (Pydantic).
        """
        logger.warning(f"Request Validation Error: {exc.errors()}")
        
        # Flatten validation errors for frontend
        flattened_errors = [
            f"{' -> '.join(str(loc) for loc in err['loc'])}: {err['msg']}"
            for err in exc.errors()
        ]
        
        return _build_response(
            status_code=422,
            error_code="UNPROCESSABLE_ENTITY",
            message="The request payload was invalid.",
            details={"errors": flattened_errors}
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Catches any unexpected Python exceptions (e.g. KeyError, TypeError).
        Ensures stack traces are logged securely on the backend but never exposed to the client.
        """
        logger.exception(f"Unhandled Server Error: {str(exc)}")
        return _build_response(
            status_code=500,
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal server error occurred."
        )
