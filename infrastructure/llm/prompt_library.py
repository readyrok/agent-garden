import logging
from dataclasses import dataclass, field
from domain.enums import PromptPattern

logger = logging.getLogger(__name__)


@dataclass
class PromptTemplate:
    name: str
    version: str
    pattern: PromptPattern
    system: str
    few_shot_examples: list[dict] = field(default_factory=list)

    def build_system_prompt(self) -> str:
        """
        Returns the full system prompt including any few-shot examples
        appended as a structured block at the end of the system string.
        """
        if not self.few_shot_examples:
            return self.system

        examples_block = "\n\nExamples:\n"
        for i, example in enumerate(self.few_shot_examples, 1):
            examples_block += f"\nExample {i}:\n"
            examples_block += f"Input: {example['input']}\n"
            examples_block += f"Output: {example['output']}\n"

        return self.system + examples_block


class PromptLibrary:
    def __init__(self):
        self._templates: dict[str, PromptTemplate] = {}

    def register(self, template: PromptTemplate) -> None:
        key = f"{template.name}:{template.version}"
        if key in self._templates:
            logger.warning("prompt_template_overwritten", extra={"key": key})
        self._templates[key] = template
        logger.info("prompt_template_registered", extra={"key": key})

    def get(self, name: str, version: str = "1.0") -> PromptTemplate:
        key = f"{name}:{version}"
        if key not in self._templates:
            raise KeyError(f"Prompt template not found: {key}. Registered: {list(self._templates.keys())}")
        return self._templates[key]

    def list_templates(self) -> list[dict]:
        return [
            {
                "name": t.name,
                "version": t.version,
                "pattern": t.pattern.value,
            }
            for t in self._templates.values()
        ]