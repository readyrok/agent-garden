from enum import Enum


class SubTaskType(str, Enum):
    CODE_REVIEW = "code_review"
    ANALYZE = "analyze"
    SUMMARIZE = "summarize"


class AgentCapability(str, Enum):
    TASK_PLANNING = "task_planning"
    CODE_REVIEW = "code_review"
    SYNTAX_CHECK = "syntax_check"
    BUG_DETECTION = "bug_detection"
    GITLAB_ANALYSIS = "gitlab_analysis"
    SUMMARIZATION = "summarization"
    REPORT_GENERATION = "report_generation"


class PromptPattern(str, Enum):
    CHAIN_OF_THOUGHT = "chain_of_thought"
    FEW_SHOT = "few_shot"
    STRUCTURED_OUTPUT = "structured_output"
    TOOL_USE = "tool_use"