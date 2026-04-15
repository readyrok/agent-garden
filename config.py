from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    anthropic_api_key: str
    jwt_secret_key: str
    jwt_expire_minutes: int = 60
    log_level: str = "INFO"
    max_retries: int = 3
    llm_timeout_seconds: int = 30
    gitlab_token: str = ""
    gitlab_url: str = "https://gitlab.com"
    mcp_filesystem_server_path: str = "infrastructure/mcp/servers/filesystem_server.py"
    mcp_code_analysis_server_path: str = "infrastructure/mcp/servers/code_analysis_server.py"
    mcp_gitlab_server_path: str = "infrastructure/mcp/servers/gitlab_server.py"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()