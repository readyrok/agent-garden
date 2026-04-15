from functools import lru_cache
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer

from config import get_settings, Settings
from infrastructure.llm.anthropic_client import AnthropicClient
from infrastructure.llm.prompt_library import PromptLibrary
from infrastructure.llm.prompts import register_all_prompts
from domain.exceptions import AuthError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


@lru_cache
def get_cached_settings() -> Settings:
    return get_settings()


@lru_cache
def get_anthropic_client() -> AnthropicClient:
    return AnthropicClient()


@lru_cache
def get_prompt_library() -> PromptLibrary:
    library = PromptLibrary()
    register_all_prompts(library)
    return library


def get_trace_id(request: Request) -> str:
    return getattr(request.state, "trace_id", "no-trace")


# Placeholder — AuthService will be implemented on Day 7.
# Defined here now so routes can depend on it from Day 2.
def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    # Temporary stub: accept any non-empty token during development.
    # Replace with real JWT verification on Day 7.
    if not token:
        raise AuthError("No token provided")
    return "dev-user"