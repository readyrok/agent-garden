import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# --- Step 1: Define your tools ---
# These are just descriptions. Claude reads them and decides when to call them.
# The actual Python functions are defined separately below.

tools = [
    {
        "name": "calculate",
        "description": "Evaluate a mathematical expression and return the result. Use this whenever the user asks for a calculation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression to evaluate, e.g. '145 * 37' or '(100 + 50) / 3'"
                }
            },
            "required": ["expression"]
        }
    },
    {
        "name": "get_weather",
        "description": "Get the current weather for a city. Use this when the user asks about weather.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city name, e.g. 'Paris' or 'New York'"
                }
            },
            "required": ["city"]
        }
    }
]

# --- Step 2: Define the actual Python functions ---
# These are fake implementations. In your real project, these call MCP servers.

def calculate(expression: str) -> str:
    try:
        result = eval(expression)  # fine for a toy example, never in production
        return f"The result of {expression} is {result}"
    except Exception as e:
        return f"Error evaluating expression: {str(e)}"

def get_weather(city: str) -> str:
    # Fake data — in the real project this calls an MCP tool
    weather_data = {
        "paris": "Partly cloudy, 18°C",
        "new york": "Sunny, 24°C",
        "london": "Rainy, 12°C",
    }
    return weather_data.get(city.lower(), f"Weather data not available for {city}")

# --- Step 3: The tool dispatcher ---
# Maps tool names to actual functions

def execute_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "calculate":
        return calculate(tool_input["expression"])
    elif tool_name == "get_weather":
        return get_weather(tool_input["city"])
    else:
        return f"Unknown tool: {tool_name}"

# --- Step 4: The agentic loop ---
# This is the core pattern your BaseAgent will use

def run_agent(user_message: str) -> str:
    print(f"\nUser: {user_message}")
    print("-" * 40)

    messages = [
        {"role": "user", "content": user_message}
    ]

    # Keep looping until Claude stops calling tools
    while True:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            tools=tools,
            messages=messages
        )

        print(f"Stop reason: {response.stop_reason}")

        # If Claude is done, return the final text response
        if response.stop_reason == "end_turn":
            # Find the text block in the response
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text

        # If Claude wants to call tools, handle them
        elif response.stop_reason == "tool_use":
            # Append Claude's response (including the tool_use blocks) to history
            messages.append({
                "role": "assistant",
                "content": response.content  # pass the full content list, not just text
            })

            # Process every tool call in this response
            # Claude might call multiple tools at once
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"Tool called: {block.name}")
                    print(f"Tool input: {json.dumps(block.input, indent=2)}")

                    # Execute the tool
                    result = execute_tool(block.name, block.input)
                    print(f"Tool result: {result}")

                    # Collect the result
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,  # must match the tool_use block id
                        "content": result
                    })

            # Append all tool results as a single user message
            messages.append({
                "role": "user",
                "content": tool_results
            })

            # Loop continues — Claude will now see the results and decide what to do next

        else:
            # Unexpected stop reason
            print(f"Unexpected stop reason: {response.stop_reason}")
            break

        print("\n--- Full message history ---")
        
        for i, msg in enumerate(messages):
            role = msg["role"]
            content = msg["content"]
            if isinstance(content, str):
                print(f"[{i}] {role}: {content[:100]}")
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        print(f"[{i}] {role}: {block.get('type', 'unknown')} block")
                    else:
                        print(f"[{i}] {role}: {block.type} block")

    return "Agent loop ended unexpectedly"


# --- Run it ---

result = run_agent("What is 145 multiplied by 37?")
print(f"\nFinal answer: {result}")

print("\n" + "="*50 + "\n")

result = run_agent("What's the weather in Paris and what is 100 divided by 4?")
print(f"\nFinal answer: {result}")