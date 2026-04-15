"""
CodeAnalysis MCP Server

Exposes Python code analysis operations as MCP tools.
Uses Python's ast module for reliable static analysis.

Run standalone for testing:
    python infrastructure/mcp/servers/code_analysis_server.py
"""
import ast
import asyncio
import logging
import textwrap
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

logger = logging.getLogger(__name__)

server = Server("code_analysis")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="count_lines",
            description=(
                "Count the number of lines in a code snippet. "
                "Returns total lines, non-empty lines, and comment lines."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The Python code to analyze"
                    }
                },
                "required": ["code"]
            }
        ),
        types.Tool(
            name="extract_functions",
            description=(
                "Extract all function and method names from Python code. "
                "Returns function names, their line numbers, and argument counts."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The Python code to analyze"
                    }
                },
                "required": ["code"]
            }
        ),
        types.Tool(
            name="check_syntax",
            description=(
                "Check if Python code has valid syntax. "
                "Returns whether it's valid and details of any syntax errors found."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The Python code to check"
                    }
                },
                "required": ["code"]
            }
        ),
    ]


@server.call_tool()
async def call_tool(
    name: str,
    arguments: dict,
) -> list[types.TextContent]:
    try:
        if name == "count_lines":
            return await _count_lines(arguments["code"])
        elif name == "extract_functions":
            return await _extract_functions(arguments["code"])
        elif name == "check_syntax":
            return await _check_syntax(arguments["code"])
        else:
            return [types.TextContent(
                type="text",
                text=f"Error: Unknown tool '{name}'"
            )]
    except Exception as e:
        logger.error(f"code_analysis_tool_error: {name} - {str(e)}")
        return [types.TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]


async def _count_lines(code: str) -> list[types.TextContent]:
    lines = code.splitlines()
    total = len(lines)
    empty = sum(1 for line in lines if not line.strip())
    comments = sum(1 for line in lines if line.strip().startswith("#"))
    code_lines = total - empty - comments

    result = (
        f"Total lines: {total}\n"
        f"Code lines: {code_lines}\n"
        f"Comment lines: {comments}\n"
        f"Empty lines: {empty}"
    )
    return [types.TextContent(type="text", text=result)]


async def _extract_functions(code: str) -> list[types.TextContent]:
    # Dedent in case the code snippet is indented
    dedented = textwrap.dedent(code)

    try:
        tree = ast.parse(dedented)
    except SyntaxError as e:
        return [types.TextContent(
            type="text",
            text=f"Cannot extract functions: syntax error at line {e.lineno}: {e.msg}"
        )]

    functions = []

    # Walk the AST and collect all function definitions
    # This catches both top-level functions and methods inside classes
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = node.args

            # Count all argument types
            arg_count = (
                len(args.args)
                + len(args.posonlyargs)
                + len(args.kwonlyargs)
                + (1 if args.vararg else 0)
                + (1 if args.kwarg else 0)
            )

            # Check for decorators
            decorators = [
                ast.unparse(d) for d in node.decorator_list
            ] if node.decorator_list else []

            is_async = isinstance(node, ast.AsyncFunctionDef)

            functions.append(
                f"{'async ' if is_async else ''}def {node.name}("
                f"{arg_count} args) at line {node.lineno}"
                + (f" [@{', @'.join(decorators)}]" if decorators else "")
            )

    if not functions:
        return [types.TextContent(
            type="text",
            text="No functions found in the provided code"
        )]

    result = f"Found {len(functions)} function(s):\n" + "\n".join(f"  - {f}" for f in functions)
    return [types.TextContent(type="text", text=result)]


async def _check_syntax(code: str) -> list[types.TextContent]:
    dedented = textwrap.dedent(code)

    try:
        ast.parse(dedented)
        # Count nodes as a basic complexity indicator
        tree = ast.parse(dedented)
        node_count = sum(1 for _ in ast.walk(tree))

        result = (
            f"Syntax: VALID\n"
            f"AST nodes: {node_count}\n"
            f"Complexity indicator: {'low' if node_count < 50 else 'medium' if node_count < 150 else 'high'}"
        )
        return [types.TextContent(type="text", text=result)]

    except SyntaxError as e:
        result = (
            f"Syntax: INVALID\n"
            f"Error: {e.msg}\n"
            f"Line: {e.lineno}\n"
            f"Column: {e.offset}\n"
            f"Text: {e.text.strip() if e.text else 'N/A'}"
        )
        return [types.TextContent(type="text", text=result)]

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Syntax: UNKNOWN - unexpected error: {str(e)}"
        )]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())