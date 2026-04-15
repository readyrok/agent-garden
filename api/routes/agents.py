from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import get_current_user

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.get("")
async def list_agents(
    current_user: str = Depends(get_current_user),
):
    # Stub — AgentRegistry wired on Day 4
    return {"agents": [], "message": "Agent registry not yet initialized"}


@router.get("/{agent_name}")
async def get_agent(
    agent_name: str,
    current_user: str = Depends(get_current_user),
):
    # Stub
    raise HTTPException(
        status_code=404,
        detail={"message": f"Agent not found: {agent_name}"}
    )