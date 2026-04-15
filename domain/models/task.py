from pydantic import BaseModel, Field
from domain.enums import SubTaskType


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
    summary: dict  # will become Summary model on Day 2
    subtasks_executed: int
    failed_subtasks: list[int] = Field(default_factory=list)
    duration_ms: int