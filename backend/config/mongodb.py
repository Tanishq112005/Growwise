import os
from typing import Optional
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

load_dotenv()

# =====================================================================
# Singleton Pattern: MongoDBManager
# =====================================================================
class MongoDBManager:
    """
    Singleton Manager for MongoDB NoSQL Database connection using Async Motor.
    Ensures a single shared connection pool across all repositories.
    """
    _instance: Optional["MongoDBManager"] = None
    _client: Optional[AsyncIOMotorClient] = None
    _db: Optional[AsyncIOMotorDatabase] = None

    def __new__(cls) -> "MongoDBManager":
        if cls._instance is None:
            cls._instance = super(MongoDBManager, cls).__new__(cls)
            cls._initialize_connection(cls._instance)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "MongoDBManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _initialize_connection(self) -> None:
        """Initializes the Async Motor MongoDB client and database reference."""
        mongodb_uri = os.getenv("MONGODB_URI") or os.getenv("DATABASE_URL") or "mongodb://localhost:27017"
        db_name = os.getenv("MONGODB_DB_NAME") or os.getenv("DATABASE_DB_NAME") or "growwise_db"

        try:
            self._client = AsyncIOMotorClient(
                mongodb_uri,
                serverSelectionTimeoutMS=5000,
                maxPoolSize=50,
                minPoolSize=10
            )
            self._db = self._client[db_name]
        except Exception as error:
            print(f"[MongoDBManager] Warning: MongoDB initialization failed: {error}")
            self._client = None
            self._db = None

    def get_database(self) -> AsyncIOMotorDatabase:
        """Returns the active MongoDB database reference."""
        if self._db is None:
            self._initialize_connection()
        if self._db is None:
            raise RuntimeError("MongoDB connection is not established.")
        return self._db

    def get_client(self) -> Optional[AsyncIOMotorClient]:
        """Returns the active AsyncIOMotorClient instance."""
        if self._client is None:
            self._initialize_connection()
        return self._client

    async def ping(self) -> bool:
        """Pings the MongoDB server to verify connectivity."""
        try:
            client = self.get_client()
            if client is not None:
                await client.admin.command('ping')
                return True
            return False
        except Exception:
            return False

    def close_connection(self) -> None:
        """Closes the MongoDB connection pool."""
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None
