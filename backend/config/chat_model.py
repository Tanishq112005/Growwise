import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from langchain_openrouter import ChatOpenRouter

load_dotenv()

# =====================================================================
# Strategy Pattern: Base Strategy for Chat Models
# =====================================================================
class BaseChatModelStrategy(ABC):
    """
    Abstract base strategy for initializing chat model providers with streaming capability.
    """
    @abstractmethod
    def create_chat_model(self, model_name: str, temperature: float, streaming: bool = True, **kwargs) -> Any:
        pass


# =====================================================================
# Concrete Strategy: OpenRouter Strategy
# =====================================================================
class OpenRouterStrategy(BaseChatModelStrategy):
    """
    Concrete strategy to initialize chat models exclusively via OpenRouter with streaming.
    Provides low-latency token-by-token streaming response delivery.
    """
    def create_chat_model(self, model_name: str, temperature: float, streaming: bool = True, **kwargs) -> Any:
        api_key = kwargs.pop("api_key", None) or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is missing in environment variables.")

        target_model = kwargs.pop("model", None) or os.getenv("OPENROUTER_MODEL") or model_name or "deepseek/deepseek-chat"

        return ChatOpenRouter(
            model=target_model,
            temperature=temperature,
            api_key=api_key,
            streaming=streaming,
            **kwargs
        )


# =====================================================================
# Singleton Pattern + Strategy Selector: ChatModelManager
# =====================================================================
class ChatModelManager:
    """
    Singleton Manager to cache and manage OpenRouter chat model instances with streaming.
    Ensures models are not re-initialized repeatedly to minimize latency.
    """
    _instance: Optional["ChatModelManager"] = None
    _model_cache: Dict[str, Any] = {}
    _strategies: Dict[str, BaseChatModelStrategy] = {}

    def __new__(cls) -> "ChatModelManager":
        if cls._instance is None:
            cls._instance = super(ChatModelManager, cls).__new__(cls)
            cls._strategies = {
                "openrouter": OpenRouterStrategy(),
            }
            cls._model_cache = {}
        return cls._instance

    @classmethod
    def get_instance(cls) -> "ChatModelManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_strategy(self, provider_name: str, strategy: BaseChatModelStrategy) -> None:
        """Register a new model strategy dynamically."""
        self._strategies[provider_name.lower()] = strategy

    def get_chat_model(
        self,
        provider: str = "openrouter",
        model_name: Optional[str] = None,
        temperature: float = 0.2,
        streaming: bool = True,
        **kwargs
    ) -> Any:
        """
        Retrieves or initializes an OpenRouter chat model with streaming support.
        """
        provider_key = provider.lower()
        if provider_key not in self._strategies:
            available = list(self._strategies.keys())
            raise ValueError(f"Provider '{provider}' not supported. Available providers: {available}")

        resolved_model = model_name or os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat")
        cache_key = f"{provider_key}::{resolved_model}::{temperature}::streaming={streaming}"

        # Return cached instance if already initialized
        if cache_key in self._model_cache:
            return self._model_cache[cache_key]

        # Use strategy to initialize new instance
        strategy = self._strategies[provider_key]
        model_instance = strategy.create_chat_model(
            model_name=resolved_model,
            temperature=temperature,
            streaming=streaming,
            **kwargs
        )

        self._model_cache[cache_key] = model_instance
        return model_instance
