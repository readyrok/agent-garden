import time
import uuid
import logging
from contextvars import ContextVar
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Context variable that stores the trace_id for the current request.
# Using contextvars means it's automatically isolated per async task —
# no risk of one request's trace_id leaking into another.
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="no-trace")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate a trace ID for this request
        trace_id = str(uuid.uuid4())
        trace_id_var.set(trace_id)

        # Store on request state so route handlers can access it via Depends
        request.state.trace_id = trace_id

        start_time = time.monotonic()

        logger.info(
            "request_started",
            extra={
                "trace_id": trace_id,
                "method": request.method,
                "path": request.url.path,
            }
        )

        try:
            response = await call_next(request)
            duration_ms = int((time.monotonic() - start_time) * 1000)

            logger.info(
                "request_completed",
                extra={
                    "trace_id": trace_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                }
            )

            # Attach trace ID to response headers so callers can reference it
            response.headers["X-Trace-ID"] = trace_id
            return response

        except Exception as e:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            logger.error(
                "request_failed",
                extra={
                    "trace_id": trace_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "duration_ms": duration_ms,
                }
            )
            raise