import asyncio
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# ─── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
async def filesystem_session():
    server_params = StdioServerParameters(
        command="python",
        args=["infrastructure/mcp/servers/filesystem_server.py"],
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


@pytest.fixture
async def code_analysis_session():
    server_params = StdioServerParameters(
        command="python",
        args=["infrastructure/mcp/servers/code_analysis_server.py"],
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


@pytest.fixture
async def gitlab_session():
    server_params = StdioServerParameters(
        command="python",
        args=["infrastructure/mcp/servers/gitlab_server.py"],
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


# ─── FileSystem server tests ───────────────────────────────────────────────────

async def test_filesystem_exposes_three_tools(filesystem_session):
    tools = await filesystem_session.list_tools()
    names = [t.name for t in tools.tools]
    assert "read_file" in names
    assert "write_file" in names
    assert "list_files" in names


async def test_filesystem_write_and_read_roundtrip(filesystem_session):
    content = "Test content for roundtrip verification"
    await filesystem_session.call_tool(
        "write_file",
        {"path": "roundtrip_test.txt", "content": content}
    )
    result = await filesystem_session.call_tool(
        "read_file",
        {"path": "roundtrip_test.txt"}
    )
    assert content in result.content[0].text


async def test_filesystem_read_nonexistent_file_returns_error(filesystem_session):
    result = await filesystem_session.call_tool(
        "read_file",
        {"path": "does_not_exist.txt"}
    )
    assert "Error" in result.content[0].text or "not found" in result.content[0].text


async def test_filesystem_path_traversal_is_blocked(filesystem_session):
    result = await filesystem_session.call_tool(
        "read_file",
        {"path": "../../.env"}
    )
    assert "Error" in result.content[0].text


async def test_filesystem_list_files_returns_written_file(filesystem_session):
    await filesystem_session.call_tool(
        "write_file",
        {"path": "list_test.txt", "content": "hello"}
    )
    result = await filesystem_session.call_tool(
        "list_files",
        {"directory": "."}
    )
    assert "list_test.txt" in result.content[0].text


# ─── CodeAnalysis server tests ─────────────────────────────────────────────────

VALID_CODE = """
def add(a: int, b: int) -> int:
    return a + b

def subtract(x, y):
    # subtract two numbers
    return x - y
"""

INVALID_CODE = """
def broken(:
    return "syntax error here"
"""


async def test_code_analysis_exposes_three_tools(code_analysis_session):
    tools = await code_analysis_session.list_tools()
    names = [t.name for t in tools.tools]
    assert "count_lines" in names
    assert "extract_functions" in names
    assert "check_syntax" in names


async def test_count_lines_returns_correct_counts(code_analysis_session):
    result = await code_analysis_session.call_tool(
        "count_lines",
        {"code": VALID_CODE}
    )
    text = result.content[0].text
    assert "Total lines" in text
    assert "Code lines" in text
    assert "Comment lines" in text


async def test_extract_functions_finds_all_functions(code_analysis_session):
    result = await code_analysis_session.call_tool(
        "extract_functions",
        {"code": VALID_CODE}
    )
    text = result.content[0].text
    assert "add" in text
    assert "subtract" in text


async def test_check_syntax_valid_code_returns_valid(code_analysis_session):
    result = await code_analysis_session.call_tool(
        "check_syntax",
        {"code": VALID_CODE}
    )
    assert "VALID" in result.content[0].text


async def test_check_syntax_invalid_code_returns_invalid(code_analysis_session):
    result = await code_analysis_session.call_tool(
        "check_syntax",
        {"code": INVALID_CODE}
    )
    assert "INVALID" in result.content[0].text


async def test_extract_functions_on_invalid_code_returns_error_not_crash(
    code_analysis_session,
):
    result = await code_analysis_session.call_tool(
        "extract_functions",
        {"code": INVALID_CODE}
    )
    # Should return an error message, not raise an exception
    assert result.content[0].text is not None
    assert "syntax error" in result.content[0].text.lower()


# ─── GitLab server tests ────────────────────────────────────────────────────────

async def test_gitlab_exposes_four_tools(gitlab_session):
    tools = await gitlab_session.list_tools()
    names = [t.name for t in tools.tools]
    assert "list_issues" in names
    assert "get_issue" in names
    assert "create_merge_request" in names
    assert "get_pipeline_status" in names


async def test_gitlab_list_issues_returns_results(gitlab_session):
    result = await gitlab_session.call_tool(
        "list_issues",
        {"project_id": "demo", "state": "opened"}
    )
    text = result.content[0].text
    assert len(text) > 0
    # Works in both mock and real mode
    assert "issue" in text.lower() or "#" in text


async def test_gitlab_get_issue_returns_details(gitlab_session):
    result = await gitlab_session.call_tool(
        "get_issue",
        {"project_id": "demo", "issue_id": 1}
    )
    text = result.content[0].text
    assert "State" in text
    assert "Description" in text


async def test_gitlab_create_mr_returns_confirmation(gitlab_session):
    result = await gitlab_session.call_tool(
        "create_merge_request",
        {
            "project_id": "demo",
            "title": "Test MR",
            "description": "Test description",
            "source_branch": "feature/test",
            "target_branch": "main"
        }
    )
    text = result.content[0].text
    assert "merge request" in text.lower() or "MR" in text


async def test_gitlab_pipeline_status_returns_status(gitlab_session):
    result = await gitlab_session.call_tool(
        "get_pipeline_status",
        {"project_id": "demo", "pipeline_id": 1}
    )
    text = result.content[0].text
    assert "Status" in text