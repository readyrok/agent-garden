class AgentGardenError(Exception):
    """Base exception for all agent garden errors."""
    def __init__(self, message: str, trace_id: str | None = None):
        super().__init__(message)
        self.trace_id = trace_id


class PipelineError(AgentGardenError):
    """Raised when the orchestration pipeline fails entirely."""
    pass


class AgentNotFoundError(AgentGardenError):
    """Raised when no agent is found for a given capability."""
    def __init__(self, capability: str, trace_id: str | None = None):
        super().__init__(f"No agent found for capability: {capability}", trace_id)
        self.capability = capability


class LLMError(AgentGardenError):
    """Raised when the LLM call fails after all retries."""
    pass


class LLMParseError(AgentGardenError):
    """Raised when the LLM response cannot be parsed into the expected model."""
    def __init__(self, raw_response: str, trace_id: str | None = None):
        super().__init__("Failed to parse LLM response into expected model", trace_id)
        self.raw_response = raw_response


class MCPError(AgentGardenError):
    """Raised when an MCP server call fails."""
    def __init__(self, server: str, tool: str, trace_id: str | None = None):
        super().__init__(f"MCP tool call failed: {server}.{tool}", trace_id)
        self.server = server
        self.tool = tool


class AuthError(AgentGardenError):
    """Raised when authentication fails."""
    pass