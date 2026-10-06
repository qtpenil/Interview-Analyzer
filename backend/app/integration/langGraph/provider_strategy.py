import abc
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from app.core.config import settings


class Provider(abc.ABC):
    """Abstract Base Class for LLM Provider Strategies."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass

    @abc.abstractmethod
    def build_model(self, api_key: str | None = None) -> Any:
        pass

    @property
    def supports_structured_output(self) -> bool:
        return True


class OpenAIProvider(Provider):
    @property
    def name(self) -> str:
        return "openai"

    def build_model(self, api_key: str | None = None) -> Any:
        key = api_key or settings.OPENAI_API_KEY
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0,
            api_key=key,
        )


class AnthropicProvider(Provider):
    @property
    def name(self) -> str:
        return "anthropic"

    def build_model(self, api_key: str | None = None) -> Any:
        key = api_key or settings.ANTHROPIC_API_KEY
        return ChatAnthropic(
            model=settings.ANTHROPIC_MODEL,
            temperature=0,
            api_key=key,
        )


class GoogleProvider(Provider):
    @property
    def name(self) -> str:
        return "google"

    def build_model(self, api_key: str | None = None) -> Any:
        keys = [k.strip() for k in settings.GEMINI_API_KEYS.split(",") if k.strip()]
        key = api_key or (keys[0] if keys else None)
        return ChatGoogleGenerativeAI(
            model=settings.GOOGLE_AI_MODEL,
            temperature=0,
            top_p=0,
            top_k=1,
            api_key=key,
        )


class OllamaProvider(Provider):
    @property
    def name(self) -> str:
        return "ollama"

    def build_model(self, api_key: str | None = None) -> Any:
        return ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            format="json",
            temperature=0,
        )


class ProviderManager:
    """Manages strategy instances for all supported providers."""

    def __init__(self):
        self._providers = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "google": GoogleProvider(),
            "ollama": OllamaProvider(),
        }

    def get_provider(self, name: str) -> Provider:
        name = name.lower()
        if name not in self._providers:
            raise ValueError(f"Unsupported provider: {name}")
        return self._providers[name]

    def get_default_provider(self) -> Provider:
        return self.get_provider(settings.PRIMARY_PROVIDER)


provider_manager = ProviderManager()
