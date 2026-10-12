import os
from typing import Optional, Any
from dotenv import load_dotenv
import redis

load_dotenv()

# =====================================================================
# Singleton Pattern: RedisConnectionManager
# =====================================================================
class RedisConnectionManager:
    """
    Singleton Manager for Redis connections and in-memory caching.
    Uses a reusable connection pool to eliminate TCP handshake latency on repetitive calls.
    """
    _instance: Optional["RedisConnectionManager"] = None
    _redis_client: Optional[redis.Redis] = None
    _connection_pool: Optional[redis.ConnectionPool] = None

    def __new__(cls) -> "RedisConnectionManager":
        if cls._instance is None:
            cls._instance = super(RedisConnectionManager, cls).__new__(cls)
            cls._initialize_connection(cls._instance)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "RedisConnectionManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _initialize_connection(self) -> None:
        """Initializes the Redis connection pool and client."""
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_password = os.getenv("REDIS_PASSWORD", None)
        redis_db = int(os.getenv("REDIS_DB", "0"))

        try:
            self._connection_pool = redis.ConnectionPool(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                db=redis_db,
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0
            )
            self._redis_client = redis.Redis(connection_pool=self._connection_pool)
        except Exception as error:
            print(f"[RedisConnectionManager] Warning: Redis initialization failed: {error}")
            self._redis_client = None

    def get_client(self) -> Optional[redis.Redis]:
        """Returns the active Redis client instance."""
        if self._redis_client is None:
            self._initialize_connection()
        return self._redis_client

    def ping(self) -> bool:
        """Pings the Redis server to verify connectivity."""
        client = self.get_client()
        if client is not None:
            try:
                return bool(client.ping())
            except Exception:
                return False
        return False
