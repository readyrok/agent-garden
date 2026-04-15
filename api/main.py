from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.logging_config import setup_logging
from api.middleware import LoggingMiddleware
from api.routes import system, auth, tasks, agents, prompts
from domain.exceptions import AgentGardenError, AuthError

# Setup logging before anything else
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs on startup and shutdown.
    On Day 6 you'll add MCP server startup here.
    On Day 4 you'll add agent registry initialization here.
    """
    logger.info("application_starting")
    yield
    logger.info("application_stopping")


app = FastAPI(
    title="Agent Garden",
    description="Multi-agent orchestration system with MCP tool integration",
    version="1.0.0",
    lifespan=lifespan,
)

# Middleware — order matters: first added is outermost
app.add_middleware(LoggingMiddleware)


# Global exception handlers — convert domain exceptions to HTTP responses.
# This is the ONLY place HTTPException concerns live for domain errors.
@app.exception_handler(AuthError)
async def auth_error_handler(request: Request, exc: AuthError):
    return JSONResponse(
        status_code=401,
        content={
            "error": "authentication_failed",
            "message": str(exc),
            "trace_id": getattr(request.state, "trace_id", "no-trace"),
        }
    )


@app.exception_handler(AgentGardenError)
async def agent_garden_error_handler(request: Request, exc: AgentGardenError):
    return JSONResponse(
        status_code=500,
        content={
            "error": type(exc).__name__,
            "message": str(exc),
            "trace_id": exc.trace_id or getattr(request.state, "trace_id", "no-trace"),
        }
    )


# Register all routers
app.include_router(system.router)
app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(agents.router)
app.include_router(prompts.router)