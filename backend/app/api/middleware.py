import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
from asgi_correlation_id import correlation_id

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract Request ID (should be set by CorrelationIdMiddleware)
        req_id = correlation_id.get() or "unknown"
        
        start_time = time.time()
        
        # Log Request (excluding sensitive paths or payloads)
        method = request.method
        path = request.url.path
        
        # Avoid logging raw bodies of uploads to prevent binary spew
        if path.startswith("/api/v1/upload"):
            logger.info(f"[{req_id}] {method} {path} - (Upload Payload)")
        else:
            logger.info(f"[{req_id}] {method} {path}")
            
        try:
            response = await call_next(request)
            
            # Calculate Duration
            process_time = time.time() - start_time
            
            # Add Custom Headers
            response.headers["X-Process-Time"] = str(process_time)
            if "X-Request-ID" not in response.headers:
                response.headers["X-Request-ID"] = req_id
                
            status_code = response.status_code
            logger.info(f"[{req_id}] {method} {path} - {status_code} - {process_time:.4f}s")
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"[{req_id}] {method} {path} - FAILED - {process_time:.4f}s - {str(e)}")
            raise e
