from typing import Any, Optional
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

# =====================================================================
# Singleton Pattern: RedisCheckpointerManager (kept name for compatibility)
# =====================================================================
class RedisCheckpointerManager:
    """
    Provides the LangGraph checkpointer used for conversation memory.

    WHY IN-MEMORY: the controller runs the graph with `ainvoke`, which needs an async-capable
    checkpointer. The sync `RedisSaver` does not support async calls and also needs Redis Stack
    (RediSearch/RedisJSON), so it failed at request time and the old construction-time fallback
    never triggered. MemorySaver is async-safe and isolates conversations by `thread_id`
    (user_id + chat_id, set in the controller). Every finished turn is also saved to MongoDB, so
    history shown in the UI survives restarts; only the model's short-term memory resets.

    To move to Redis later, swap this for `AsyncRedisSaver` and call its async setup at startup.
    """
    _instance: Optional["RedisCheckpointerManager"] = None
    _shared_checkpointer: Optional[Any] = None

    def __new__(cls) -> "RedisCheckpointerManager":
        if cls._instance is None:
            cls._instance = super(RedisCheckpointerManager, cls).__new__(cls)
            cls._shared_checkpointer = MemorySaver()
        return cls._instance

    @classmethod
    def get_instance(cls) -> "RedisCheckpointerManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_checkpointer(self, user_id: str) -> Any:
        """Returns the shared checkpointer. Isolation between users/chats comes from thread_id."""
        if not user_id:
            raise ValueError("user_id is required to fetch a checkpointer.")
        return self._shared_checkpointer
