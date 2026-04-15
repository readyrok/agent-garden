import logging
from anthropic import Anthropic, APIError, RateLimitError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from config import get_settings

logger = logging.getLogger(__name__)


class AnthropicClient:
    def __init__(self):
        settings = get_settings()
        self._client = Anthropic(api_key=settings.anthropic_api_key)
        self._model = "claude-sonnet-4-5"
        self._timeout = settings.llm_timeout_seconds
        self._max_retries = settings.max_retries

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(RateLimitError),
    )
    def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        system: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ):
        kwargs = {
            "model": self._model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = tools

        logger.debug("llm_request", extra={
            "message_count": len(messages),
            "has_tools": tools is not None,
        })

        response = self._client.messages.create(**kwargs)

        logger.debug("llm_response", extra={
            "stop_reason": response.stop_reason,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        })

        return response