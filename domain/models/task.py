from pydantic import BaseModel, Field
from domain.enums import SubTaskType
from domain.models.agent import Summary


class SubTask(BaseModel):
    id: int
    type: SubTaskType
    description: str
    input_data: str


class TaskPlan(BaseModel):
    original_task: str
    subtasks: list[SubTask]
    reasoning: str


class TaskRequest(BaseModel):
    task: str
    save_to_file: bool = False


class TaskResponse(BaseModel):
    trace_id: str
    summary: Summary
    subtasks_executed: int
    failed_subtasks: list[int] = Field(default_factory=list)
    duration_ms: int


class TaskResult(BaseModel):
    """Internal model passed between Orchestrator and agents."""
    subtask_id: int
    agent_name: str
    output: dict
    duration_ms: int