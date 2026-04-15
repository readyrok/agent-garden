"""
Run this to verify your Day 1 setup is complete.
Delete this file on Day 2.
"""
import sys


def check(label, fn):
    try:
        fn()
        print(f"  [OK] {label}")
    except Exception as e:
        print(f"  [FAIL] {label}: {e}")
        sys.exit(1)


print("Running Day 1 sanity checks...\n")

check("Python version >= 3.11", lambda: (
    __import__("sys"),
    None if __import__("sys").version_info >= (3, 11)
    else (_ for _ in ()).throw(RuntimeError("Need Python 3.11+"))
))

check("Config loads from .env", lambda: (
    __import__("config").get_settings()
))

check("Anthropic API key is set", lambda: (
    s := __import__("config").get_settings(),
    None if s.anthropic_api_key
    else (_ for _ in ()).throw(ValueError("ANTHROPIC_API_KEY not set"))
))

check("Domain models import", lambda: (
    __import__("domain.models.task", fromlist=["TaskRequest"]),
    __import__("domain.models.agent", fromlist=["CodeReview"]),
    __import__("domain.models.auth", fromlist=["User"]),
))

check("AnthropicClient initializes", lambda: (
    __import__("infrastructure.llm.anthropic_client", fromlist=["AnthropicClient"]).AnthropicClient()
))

check("AnthropicClient makes a real API call", lambda: (
    client := __import__("infrastructure.llm.anthropic_client", fromlist=["AnthropicClient"]).AnthropicClient(),
    response := client.complete([{"role": "user", "content": "Say the word OK and nothing else"}]),
    None if "ok" in response.content[0].text.lower()
    else (_ for _ in ()).throw(ValueError(f"Unexpected response: {response.content[0].text}"))
))

print("\nAll checks passed. Day 1 complete.")