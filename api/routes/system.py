from fastapi import APIRouter

router = APIRouter(tags=["System"])


@router.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}


@router.get("/mcp/status")
async def mcp_status():
    # Stub — real implementation on Day 6 when MCPServerManager exists
    return {
        "servers": [],
        "message": "MCP server manager not yet initialized"
    }