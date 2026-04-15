"""
GitLab MCP Server

Exposes GitLab API operations as MCP tools.
Operates in real mode when GITLAB_TOKEN is set in environment,
mock mode otherwise — so the project works without a GitLab account.

Run standalone for testing:
    python infrastructure/mcp/servers/gitlab_server.py
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

logger = logging.getLogger(__name__)

# Determine mode at startup
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN", "")
GITLAB_URL = os.getenv("GITLAB_URL", "https://gitlab.com")
USE_MOCK = not GITLAB_TOKEN

if not USE_MOCK:
    try:
        import gitlab
        gl = gitlab.Gitlab(GITLAB_URL, private_token=GITLAB_TOKEN)
        gl.auth()
        logger.info("gitlab_server_mode: real (authenticated)")
    except Exception as e:
        logger.warning(f"GitLab auth failed, falling back to mock mode: {e}")
        USE_MOCK = True
else:
    logger.info("gitlab_server_mode: mock (no GITLAB_TOKEN set)")

server = Server("gitlab")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    mode_note = " (mock mode — set GITLAB_TOKEN for real data)" if USE_MOCK else ""

    return [
        types.Tool(
            name="list_issues",
            description=(
                f"List issues from a GitLab project{mode_note}. "
                "Returns issue IDs, titles, states, and assignees."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The GitLab project ID or path, e.g. '42' or 'mygroup/myproject'"
                    },
                    "state": {
                        "type": "string",
                        "description": "Filter by state: 'opened', 'closed', or 'all'",
                        "enum": ["opened", "closed", "all"],
                        "default": "opened"
                    }
                },
                "required": ["project_id"]
            }
        ),
        types.Tool(
            name="get_issue",
            description=(
                f"Get details of a specific GitLab issue{mode_note}. "
                "Returns full issue details including description and comments."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The GitLab project ID or path"
                    },
                    "issue_id": {
                        "type": "integer",
                        "description": "The issue IID (internal ID within the project)"
                    }
                },
                "required": ["project_id", "issue_id"]
            }
        ),
        types.Tool(
            name="create_merge_request",
            description=(
                f"Create a merge request in a GitLab project{mode_note}."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The GitLab project ID or path"
                    },
                    "title": {
                        "type": "string",
                        "description": "Title of the merge request"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the changes"
                    },
                    "source_branch": {
                        "type": "string",
                        "description": "The branch containing your changes"
                    },
                    "target_branch": {
                        "type": "string",
                        "description": "The branch to merge into, e.g. 'main'"
                    }
                },
                "required": [
                    "project_id", "title", "description",
                    "source_branch", "target_branch"
                ]
            }
        ),
        types.Tool(
            name="get_pipeline_status",
            description=(
                f"Get the status of a GitLab CI/CD pipeline{mode_note}."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The GitLab project ID or path"
                    },
                    "pipeline_id": {
                        "type": "integer",
                        "description": "The pipeline ID"
                    }
                },
                "required": ["project_id", "pipeline_id"]
            }
        ),
    ]


@server.call_tool()
async def call_tool(
    name: str,
    arguments: dict,
) -> list[types.TextContent]:
    try:
        if USE_MOCK:
            return await _call_mock_tool(name, arguments)
        else:
            return await _call_real_tool(name, arguments)
    except Exception as e:
        logger.error(f"gitlab_tool_error: {name} - {str(e)}")
        return [types.TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]


# ─── Real GitLab implementation ───────────────────────────────────────────────

async def _call_real_tool(
    name: str,
    arguments: dict,
) -> list[types.TextContent]:
    if name == "list_issues":
        return await _real_list_issues(
            arguments["project_id"],
            arguments.get("state", "opened")
        )
    elif name == "get_issue":
        return await _real_get_issue(
            arguments["project_id"],
            arguments["issue_id"]
        )
    elif name == "create_merge_request":
        return await _real_create_mr(arguments)
    elif name == "get_pipeline_status":
        return await _real_get_pipeline(
            arguments["project_id"],
            arguments["pipeline_id"]
        )
    else:
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]


async def _real_list_issues(
    project_id: str,
    state: str,
) -> list[types.TextContent]:
    project = gl.projects.get(project_id)
    issues = project.issues.list(state=state, all=True)

    if not issues:
        return [types.TextContent(
            type="text",
            text=f"No {state} issues found in project {project_id}"
        )]

    lines = [f"Found {len(issues)} {state} issue(s) in project {project_id}:\n"]
    for issue in issues[:20]:  # cap at 20 to avoid token overflow
        assignee = issue.assignee["name"] if issue.assignee else "unassigned"
        lines.append(
            f"  #{issue.iid}: {issue.title}\n"
            f"    State: {issue.state} | Assignee: {assignee} | "
            f"Created: {issue.created_at[:10]}"
        )

    return [types.TextContent(type="text", text="\n".join(lines))]


async def _real_get_issue(
    project_id: str,
    issue_id: int,
) -> list[types.TextContent]:
    project = gl.projects.get(project_id)
    issue = project.issues.get(issue_id)

    assignee = issue.assignee["name"] if issue.assignee else "unassigned"
    labels = ", ".join(issue.labels) if issue.labels else "none"

    result = (
        f"Issue #{issue.iid}: {issue.title}\n"
        f"State: {issue.state}\n"
        f"Assignee: {assignee}\n"
        f"Labels: {labels}\n"
        f"Created: {issue.created_at[:10]}\n"
        f"Updated: {issue.updated_at[:10]}\n\n"
        f"Description:\n{issue.description or 'No description provided'}"
    )

    return [types.TextContent(type="text", text=result)]


async def _real_create_mr(arguments: dict) -> list[types.TextContent]:
    project = gl.projects.get(arguments["project_id"])
    mr = project.mergerequests.create({
        "title": arguments["title"],
        "description": arguments["description"],
        "source_branch": arguments["source_branch"],
        "target_branch": arguments["target_branch"],
    })

    result = (
        f"Merge request created successfully.\n"
        f"MR !{mr.iid}: {mr.title}\n"
        f"URL: {mr.web_url}\n"
        f"State: {mr.state}"
    )
    return [types.TextContent(type="text", text=result)]


async def _real_get_pipeline(
    project_id: str,
    pipeline_id: int,
) -> list[types.TextContent]:
    project = gl.projects.get(project_id)
    pipeline = project.pipelines.get(pipeline_id)

    duration = f"{pipeline.duration}s" if pipeline.duration else "N/A"

    result = (
        f"Pipeline #{pipeline.id}\n"
        f"Status: {pipeline.status}\n"
        f"Branch: {pipeline.ref}\n"
        f"Duration: {duration}\n"
        f"Created: {pipeline.created_at[:19]}\n"
        f"URL: {pipeline.web_url}"
    )
    return [types.TextContent(type="text", text=result)]


# ─── Mock implementation ───────────────────────────────────────────────────────

async def _call_mock_tool(
    name: str,
    arguments: dict,
) -> list[types.TextContent]:
    """
    Returns realistic mock data when no GITLAB_TOKEN is configured.
    Demonstrates the full tool interface without needing a real GitLab instance.
    """
    if name == "list_issues":
        return _mock_list_issues(
            arguments["project_id"],
            arguments.get("state", "opened")
        )
    elif name == "get_issue":
        return _mock_get_issue(
            arguments["project_id"],
            arguments["issue_id"]
        )
    elif name == "create_merge_request":
        return _mock_create_mr(arguments)
    elif name == "get_pipeline_status":
        return _mock_get_pipeline(
            arguments["project_id"],
            arguments["pipeline_id"]
        )
    else:
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]


def _mock_list_issues(
    project_id: str,
    state: str,
) -> list[types.TextContent]:
    text = (
        f"[MOCK] Found 3 {state} issue(s) in project {project_id}:\n\n"
        f"  #1: Authentication fails for users with special characters in password\n"
        f"    State: {state} | Assignee: alice | Created: 2024-11-01\n\n"
        f"  #2: API response time exceeds 2s under load\n"
        f"    State: {state} | Assignee: bob | Created: 2024-11-03\n\n"
        f"  #3: Missing error handling in file upload endpoint\n"
        f"    State: {state} | Assignee: unassigned | Created: 2024-11-05"
    )
    return [types.TextContent(type="text", text=text)]


def _mock_get_issue(
    project_id: str,
    issue_id: int,
) -> list[types.TextContent]:
    text = (
        f"[MOCK] Issue #{issue_id}: Authentication fails for users with "
        f"special characters in password\n"
        f"State: opened\n"
        f"Assignee: alice\n"
        f"Labels: bug, authentication\n"
        f"Created: 2024-11-01\n"
        f"Updated: 2024-11-06\n\n"
        f"Description:\n"
        f"When a user has special characters (e.g. @, #, !) in their password,\n"
        f"the login endpoint returns a 500 error instead of authenticating correctly.\n\n"
        f"Steps to reproduce:\n"
        f"1. Create a user with password 'P@ssw0rd!'\n"
        f"2. Attempt to login via POST /auth/token\n"
        f"3. Observe 500 Internal Server Error\n\n"
        f"Expected: 200 OK with JWT token\n"
        f"Actual: 500 error, log shows 'invalid escape sequence'"
    )
    return [types.TextContent(type="text", text=text)]


def _mock_create_mr(arguments: dict) -> list[types.TextContent]:
    text = (
        f"[MOCK] Merge request created successfully.\n"
        f"MR !42: {arguments['title']}\n"
        f"URL: https://gitlab.com/demo/project/-/merge_requests/42\n"
        f"State: opened\n"
        f"Source: {arguments['source_branch']} → Target: {arguments['target_branch']}"
    )
    return [types.TextContent(type="text", text=text)]


def _mock_get_pipeline(
    project_id: str,
    pipeline_id: int,
) -> list[types.TextContent]:
    text = (
        f"[MOCK] Pipeline #{pipeline_id}\n"
        f"Status: passed\n"
        f"Branch: main\n"
        f"Duration: 127s\n"
        f"Created: 2024-11-06T14:23:00\n"
        f"URL: https://gitlab.com/demo/project/-/pipelines/{pipeline_id}"
    )
    return [types.TextContent(type="text", text=text)]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())