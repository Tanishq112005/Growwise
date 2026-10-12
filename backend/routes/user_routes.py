from typing import Dict, Any
from fastapi import APIRouter, status
from backend.controllers.user_controller import (
    UserController,
    SignUpRequest,
    LoginRequest,
    CreateUserRequest,
    UpdateTokenRequest,
)

user_router = APIRouter(prefix="/users", tags=["Users"])
_user_controller = UserController()


@user_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup_route(payload: SignUpRequest) -> Dict[str, Any]:
    """Route: Registers a new user with email and password."""
    return await _user_controller.signup(payload)


@user_router.post("/login", status_code=status.HTTP_200_OK)
async def login_route(payload: LoginRequest) -> Dict[str, Any]:
    """Route: Authenticates an existing user with email and password."""
    return await _user_controller.login(payload)


@user_router.post("", status_code=status.HTTP_201_CREATED)
async def create_user_route(payload: CreateUserRequest) -> Dict[str, Any]:
    """Route: Creates a new user profile with auto-assigned UUID."""
    return await _user_controller.create_user(payload)


@user_router.get("/{user_id}")
async def get_user_by_id_route(user_id: str) -> Dict[str, Any]:
    """Route: Retrieves a user profile by UUID."""
    return await _user_controller.get_user_by_id(user_id)


@user_router.get("/phone/{phone_number}")
async def get_user_by_phone_route(phone_number: str) -> Dict[str, Any]:
    """Route: Retrieves a user profile by mobile phone number."""
    return await _user_controller.get_user_by_phone(phone_number)


@user_router.put("/{user_id}/token")
async def update_token_route(user_id: str, payload: UpdateTokenRequest) -> Dict[str, Any]:
    """Route: Updates the auth refresh token for a user."""
    return await _user_controller.update_refresh_token(user_id, payload)
