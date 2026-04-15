import pytest
from infrastructure.llm.prompt_library import PromptLibrary, PromptTemplate
from infrastructure.llm.prompts import register_all_prompts
from domain.enums import PromptPattern


@pytest.fixture
def library() -> PromptLibrary:
    lib = PromptLibrary()
    register_all_prompts(lib)
    return lib


def test_all_templates_registered(library):
    templates = library.list_templates()
    names = [t["name"] for t in templates]
    assert "planner" in names
    assert "coder" in names
    assert "summarizer" in names


def test_get_template_returns_correct_template(library):
    planner = library.get("planner", "1.0")
    assert planner.name == "planner"
    assert planner.version == "1.0"
    assert planner.pattern == PromptPattern.FEW_SHOT


def test_get_missing_template_raises_key_error(library):
    with pytest.raises(KeyError, match="not found"):
        library.get("nonexistent", "1.0")


def test_build_system_prompt_includes_few_shot_examples(library):
    planner = library.get("planner", "1.0")
    prompt = planner.build_system_prompt()
    assert "Example 1" in prompt
    assert "Example 2" in prompt


def test_build_system_prompt_without_examples_returns_system_only(library):
    coder = library.get("coder", "1.0")
    prompt = coder.build_system_prompt()
    assert "Example 1" not in prompt
    assert prompt == coder.system


def test_register_overwrites_existing_template(library):
    new_template = PromptTemplate(
        name="planner",
        version="1.0",
        pattern=PromptPattern.CHAIN_OF_THOUGHT,
        system="Updated system prompt",
    )
    library.register(new_template)
    retrieved = library.get("planner", "1.0")
    assert retrieved.system == "Updated system prompt"


def test_planner_prompt_contains_json_schema_instruction(library):
    planner = library.get("planner", "1.0")
    assert "original_task" in planner.system
    assert "subtasks" in planner.system
    assert "reasoning" in planner.system


def test_coder_prompt_contains_tool_workflow(library):
    coder = library.get("coder", "1.0")
    assert "count_lines" in coder.system
    assert "extract_functions" in coder.system
    assert "check_syntax" in coder.system


def test_list_templates_returns_correct_structure(library):
    templates = library.list_templates()
    for t in templates:
        assert "name" in t
        assert "version" in t
        assert "pattern" in t