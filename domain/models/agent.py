from pydantic import BaseModel, Field
from typing import Literal


class CodeReview(BaseModel):
    findings: list[str]
    severity: Literal["low", "medium", "high"]
    suggested_changes: str
    explanation: str
    lines_of_code: int
    functions_found: list[str] = Field(default_factory=list)


class Summary(BaseModel):
    title: str
    executive_summary: str
    key_findings: list[str]
    recommendations: list[str]
    output_file: str | None = None


class AgentManifest(BaseModel):
    name: str
    version: str
    description: str
    capabilities: list[str]
    required_mcp_servers: list[str]
    author: str = "agent-garden"