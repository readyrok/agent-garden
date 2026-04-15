from fastapi import APIRouter, Depends, HTTPException
from domain.models.task import TaskRequest, TaskResponse
from domain.models.agent import Summary
from domain.exceptions import AgentGardenError
from api.dependencies import get_current_user, get_trace_id

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/run-task", response_model=TaskResponse)
async def run_task(
    request: TaskRequest,
    trace_id: str = Depends(get_trace_id),
    current_user: str = Depends(get_current_user),
):
    # Stub — real implementation wires OrchestrationService on Day 6
    raise HTTPException(
        status_code=501,
        detail={"message": "Not yet implemented", "trace_id": trace_id}
    )


@router.get("/tasks/{trace_id_param}")
async def get_task_result(
    trace_id_param: str,
    current_user: str = Depends(get_current_user),
):
    # Stub — in-memory store wired on Day 6
    raise HTTPException(
        status_code=404,
        detail={"message": f"No result found for trace_id: {trace_id_param}"}
    )