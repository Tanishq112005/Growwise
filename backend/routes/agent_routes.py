from typing import Dict, Any
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from backend.controllers.agent_controller import (
    AgentController,
    ChatRequest,
)

agent_router = APIRouter(prefix="/agent", tags=["Agent"])
_agent_controller = AgentController()


@agent_router.post("/stream")
async def chat_stream_route(payload: ChatRequest) -> StreamingResponse:
    """Route: Server-Sent Events (SSE) streaming chat endpoint."""
    return await _agent_controller.stream_chat(payload)


@agent_router.post("/chat")
async def chat_sync_route(payload: ChatRequest) -> Dict[str, Any]:
    """Route: Synchronous chat turn endpoint returning JSON response."""
    return await _agent_controller.sync_chat(payload)


@agent_router.get("/chats/{user_id}")
async def get_all_chats_route(user_id: str) -> Dict[str, Any]:
    """Route: Retrieves all chat sessions for a user."""
    return await _agent_controller.get_all_chats(user_id)


@agent_router.get("/chats/{user_id}/{chat_id}")
async def get_chat_session_route(user_id: str, chat_id: str) -> Dict[str, Any]:
    """Route: Retrieves message turns for a specific chat session."""
    return await _agent_controller.get_chat_session(user_id, chat_id)


@agent_router.delete("/chats/{user_id}/{chat_id}")
async def delete_chat_session_route(user_id: str, chat_id: str) -> Dict[str, Any]:
    """Route: Deletes a specific chat session."""
    return await _agent_controller.delete_chat_session(user_id, chat_id)
