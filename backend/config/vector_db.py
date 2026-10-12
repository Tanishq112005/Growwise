import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

# =====================================================================
# Strategy Pattern: Base Strategy for Vector Databases
# =====================================================================
class BaseVectorDbStrategy(ABC):
    """
    Abstract base strategy for vector database connections and operations.
    """
    @abstractmethod
    def initialize_client(self, **kwargs) -> Any:
        pass

    @abstractmethod
    def get_index(self, index_name: str, **kwargs) -> Any:
        pass


# =====================================================================
# Concrete Strategy: Pinecone Vector Database Strategy
# =====================================================================
class PineconeStrategy(BaseVectorDbStrategy):
    """
    Concrete strategy to connect and manage Pinecone vector database.
    """
    def __init__(self):
        self._client: Optional[Pinecone] = None

    def initialize_client(self, **kwargs) -> Pinecone:
        api_key = kwargs.get("api_key") or os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY is missing in environment variables.")

        self._client = Pinecone(api_key=api_key)
        return self._client

    def get_index(self, index_name: str, **kwargs) -> Any:
        if self._client is None:
            self.initialize_client(**kwargs)
        return self._client.Index(index_name)


# =====================================================================
# Singleton Pattern + Strategy Selector: VectorDbManager
# =====================================================================
class VectorDbManager:
    """
    Singleton Manager for Vector Databases.
    Prevents repeated connection handshakes, reducing query latency and resource overhead.
    """
    _instance: Optional["VectorDbManager"] = None
    _strategies: Dict[str, BaseVectorDbStrategy] = {}
    _index_cache: Dict[str, Any] = {}

    def __new__(cls) -> "VectorDbManager":
        if cls._instance is None:
            cls._instance = super(VectorDbManager, cls).__new__(cls)
            cls._strategies = {
                "pinecone": PineconeStrategy()
            }
            cls._index_cache = {}
        return cls._instance

    @classmethod
    def get_instance(cls) -> "VectorDbManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_strategy(self, provider_name: str, strategy: BaseVectorDbStrategy) -> None:
        """Register a new vector database strategy dynamically."""
        self._strategies[provider_name.lower()] = strategy

    def get_index(
        self,
        provider: str = "pinecone",
        index_name: str = "groww-genz-knowledge",
        **kwargs
    ) -> Any:
        """
        Retrieves or initializes a vector index using Singleton caching and Strategy execution.
        """
        provider_key = provider.lower()
        if provider_key not in self._strategies:
            available = list(self._strategies.keys())
            raise ValueError(f"Vector DB provider '{provider}' not supported. Available: {available}")

        cache_key = f"{provider_key}::{index_name}"
        if cache_key in self._index_cache:
            return self._index_cache[cache_key]

        strategy = self._strategies[provider_key]
        index_instance = strategy.get_index(index_name=index_name, **kwargs)
        self._index_cache[cache_key] = index_instance
        return index_instance
