from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import HTTPException, status
from backend.repositories.user_repository import UserRepository


# =====================================================================
# Request / Response Schemas
# =====================================================================
class SignUpRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Full name of the user")
    email: str = Field(..., min_length=3, description="Email address for login")
    password: str = Field(..., min_length=6, description="Password (at least 6 characters)")
    phone_number: Optional[str] = Field(None, description="Optional mobile phone number")


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, description="Email address for login")
    password: str = Field(..., min_length=1, description="Password")


class CreateUserRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Full name of the user")
    phone_number: str = Field(..., min_length=10, description="Mobile phone number")


class UpdateTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1, description="New auth refresh token")


# =====================================================================
# User Controller: UserController
# =====================================================================
class UserController:
    """
    Controller handling business logic for user profiles,
    registration, UUID assignments, and authentication tokens.
    """
    def __init__(self, user_repo: Optional[UserRepository] = None):
        self._user_repo = user_repo or UserRepository()

    async def signup(self, payload: SignUpRequest) -> Dict[str, Any]:
        """
        Registers a new user with name, email, password, and auto-generated UUID.
        """
        try:
            user = await self._user_repo.create_user(
                name=payload.name,
                email=payload.email,
                password=payload.password,
                phone_number=payload.phone_number
            )
            return {
                "status": "success",
                "message": "User registered successfully.",
                "user": user,
                "token": user.get("refresh_token")
            }
        except ValueError as ve:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(ve)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to sign up user: {str(e)}"
            )

    async def login(self, payload: LoginRequest) -> Dict[str, Any]:
        """
        Authenticates a user via email and password, returning their profile and session token.
        """
        try:
            user = await self._user_repo.authenticate_user(
                email=payload.email,
                password=payload.password
            )
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password."
                )
            return {
                "status": "success",
                "message": "Login successful.",
                "user": user,
                "token": user.get("refresh_token")
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to authenticate user: {str(e)}"
            )

    async def create_user(self, payload: CreateUserRequest) -> Dict[str, Any]:
        """
        Creates a new user profile with auto-assigned UUID and initialized empty portfolio/goals.
        """
        try:
            existing = await self._user_repo.get_user_by_phone(payload.phone_number)
            if existing:
                return {
                    "status": "success",
                    "message": "User already registered.",
                    "user": existing
                }

            new_user = await self._user_repo.create_user(
                name=payload.name,
                phone_number=payload.phone_number
            )
            return {
                "status": "success",
                "message": "User created successfully.",
                "user": new_user
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create user: {str(e)}"
            )

    async def get_user_by_id(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieves a user profile by UUID.
        """
        try:
            user = await self._user_repo.get_user_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with id '{user_id}' was not found."
                )
            return {
                "status": "success",
                "user": user
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch user: {str(e)}"
            )

    async def get_user_by_phone(self, phone_number: str) -> Dict[str, Any]:
        """
        Retrieves a user profile by mobile phone number.
        """
        try:
            user = await self._user_repo.get_user_by_phone(phone_number)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with phone '{phone_number}' was not found."
                )
            return {
                "status": "success",
                "user": user
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch user by phone: {str(e)}"
            )

    async def update_refresh_token(self, user_id: str, payload: UpdateTokenRequest) -> Dict[str, Any]:
        """
        Updates the auth refresh token for a user.
        """
        try:
            updated = await self._user_repo.update_refresh_token(
                user_id=user_id,
                refresh_token=payload.refresh_token
            )
            if not updated:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with id '{user_id}' was not found."
                )
            return {
                "status": "success",
                "message": "Refresh token updated successfully."
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update refresh token: {str(e)}"
            )
