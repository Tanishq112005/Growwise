import uuid
from typing import Dict, Any, Optional
from backend.config.mongodb import MongoDBManager
from backend.utils.auth_utils import hash_password, verify_password

# =====================================================================
# User Repository: UserRepository
# =====================================================================
class UserRepository:
    """
    Repository managing user creation, retrieval, and profile authentication tokens.
    """
    def __init__(self, collection=None):
        self._db_manager = MongoDBManager.get_instance()
        self._collection_override = collection

    @property
    def _collection(self):
        if self._collection_override is not None:
            return self._collection_override
        return self._db_manager.get_database()["users"]

    async def create_user(
        self,
        name: str,
        phone_number: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates a new user with an automatically assigned UUID and initial empty stores.
        Supports email + password authentication and phone number registration.
        """
        if not name or not name.strip():
            raise ValueError("Name is required to create a user.")
        if not phone_number and not email:
            raise ValueError("Either email or phone number is required to create a user.")

        clean_name = name.strip()
        clean_email = email.strip().lower() if email else None
        clean_phone = phone_number.strip() if phone_number else None

        if clean_email:
            existing_email = await self._collection.find_one({"email": clean_email})
            if existing_email:
                raise ValueError(f"User with email '{clean_email}' already exists.")

        if clean_phone:
            existing_phone = await self._collection.find_one({"phone_number": clean_phone})
            if existing_phone:
                raise ValueError(f"User with phone number '{clean_phone}' already exists.")

        password_hash = hash_password(password) if password else None
        generated_user_id = str(uuid.uuid4())
        session_token = str(uuid.uuid4())

        user_doc: Dict[str, Any] = {
            "user_id": generated_user_id,
            "name": clean_name,
            "email": clean_email,
            "phone_number": clean_phone,
            "password_hash": password_hash,
            "refresh_token": session_token,
            "current_list_of_the_stocks": [],
            "goals": [],
            "user_chat_history": {},
            "recently_veiwed_stock": []
        }

        await self._collection.insert_one(user_doc)
        
        # Return clean copy without MongoDB internal _id or password_hash
        clean_user = dict(user_doc)
        clean_user.pop("_id", None)
        clean_user.pop("password_hash", None)
        return clean_user

    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Validates user credentials by email and password.
        Returns the user document (without password hash) with a fresh session token if valid,
        or None if credentials do not match.
        """
        if not email or not password:
            return None

        clean_email = email.strip().lower()
        user = await self._collection.find_one({"email": clean_email})
        if not user:
            return None

        stored_hash = user.get("password_hash")
        if not stored_hash or not verify_password(password, stored_hash):
            return None

        # Issue fresh refresh token upon successful authentication
        new_token = str(uuid.uuid4())
        await self.update_refresh_token(user["user_id"], new_token)
        user["refresh_token"] = new_token

        # Clean sensitive fields before returning
        user.pop("_id", None)
        user.pop("password_hash", None)
        return user

    async def ensure_user(self, user_id: str) -> None:
        """
        Guarantees a user document exists (guest users created on first contact).
        Without this, goal creation raises 'user does not exist' and chat turns fail to save
        silently, because those writes use update_one without upsert.
        """
        if not user_id:
            raise ValueError("user_id is required.")
        await self._collection.update_one(
            {"user_id": user_id},
            {"$setOnInsert": {
                "name": "Guest",
                "email": None,
                "phone_number": None,
                "password_hash": None,
                "refresh_token": None,
                "current_list_of_the_stocks": [],
                "goals": [],
                "user_chat_history": {},
                "recently_veiwed_stock": []
            }},
            upsert=True
        )

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a user document by user_id UUID, excluding sensitive password hash."""
        return await self._collection.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Retrieves a user document by email, excluding sensitive password hash."""
        return await self._collection.find_one({"email": email.strip().lower()}, {"_id": 0, "password_hash": 0})

    async def get_user_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Retrieves a user document by mobile phone number, excluding sensitive password hash."""
        return await self._collection.find_one({"phone_number": phone_number.strip()}, {"_id": 0, "password_hash": 0})

    async def update_refresh_token(self, user_id: str, refresh_token: str) -> bool:
        """Updates the auth refresh token for a user."""
        result = await self._collection.update_one(
            {"user_id": user_id},
            {"$set": {"refresh_token": refresh_token}}
        )
        return result.modified_count > 0
