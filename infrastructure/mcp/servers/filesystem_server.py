"""
FileSystem MCP Server

Exposes file system operations as MCP tools.
Agents use this to read files, write reports, and list directories.

Run standalone for testing:
    python infrastructure/mcp/servers/filesystem_server.py
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types


logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

ALLOWED_BASE_PATH = Path("output").resolve()

def _ensure_output_dir() -> None:
    ALLOWED_BASE_PATH.mkdir(parents=True, exist_ok=True)

def _safe_path(path_str: str) -> Path:
    resolved = (ALLOWED_BASE_PATH / path_str).resolve()
    if not str(resolved).startswith(str(ALLOWED_BASE_PATH)):
        raise ValueError(f"Path '{path_str}' is outside the allowed directory")
    return resolved

server = Server("filesystem")

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="read_file",
            description=(
                "Read the contents of a file. "
                "Path is relative to the output directory."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative file path to read"
                    }
                },
                "required": ["path"]
            }
        ),
        types.Tool(
            name="write_file",
            description=(
                "Write content to a file. "
                "Path is relative to the output directory."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative file path to write to"
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file"
                    }
                },
                "required": ["path", "content"]
            }
        ),
        types.Tool(
            name="list_files",
            description=(
                "List all files in a directory. "
                "Pass '.' to list the root output directory."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Relative directory path to list"
                    }
                },
                "required": ["directory"]
            }
        )
    ]

@server.call_tool()
async def call_tool(
    name: str,
    arguments: dict
) -> list[types.TextContent]:
    _ensure_output_dir()

    try:
        if name == "read_file":
            return await _read_file(arguments["path"])
        elif name == "write_file":
            return await _write_file(arguments["path"], arguments["content"])
        elif name == "list_files":  # ✅ Fix 2: was "list_file", now matches tool name
            return await _list_files(arguments["directory"])
        else:
            return [types.TextContent(
                type="text",
                text=f"Error: Unknown tool '{name}'"
            )]

    except ValueError as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.error(f"filesystem_tool_error: {name} - {str(e)}")
        return [types.TextContent(type="text", text=f"Error executing {name}: {str(e)}")]

async def _read_file(path_str: str) -> list[types.TextContent]:
    path = _safe_path(path_str)
    if not path.exists():
        return [types.TextContent(
            type="text",
            text=f"Error: File not found: {path_str}"
        )]
    content = path.read_text(encoding="utf-8")
    return [types.TextContent(type="text", text=content)]

async def _write_file(
        path_str: str,
        content: str
) -> list[types.TextContent]:
    path = _safe_path(path_str)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    # ✅ Fix 3: was returning bare TextContent, now wrapped in a list
    return [types.TextContent(
        type="text",
        text=f"Successfully wrote {len(content)} characters to {path_str}"
    )]

async def _list_files(directory_str: str) -> list[types.TextContent]:
    path = _safe_path(directory_str)
    if not path.exists():
        return [types.TextContent(
            type="text",
            text=f"Error: Directory not found: {directory_str}"
        )]
    if not path.is_dir():
        return [types.TextContent(
            type="text",
            text=f"Error: Not a directory: {directory_str}"
        )]

    files = []
    for item in sorted(path.iterdir()):
        item_type = "dir" if item.is_dir() else "file"
        size = item.stat().st_size if item.is_file() else 0
        files.append(f"{item_type}: {item.name} ({size} bytes)")

    if not files:
        return [types.TextContent(type="text", text="Directory is empty")]

    return [types.TextContent(type="text", text="\n".join(files))]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())