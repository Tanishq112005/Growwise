import os
import sys
from pathlib import Path

# Automatically ensure project root is on sys.path so backend works whether run
# from root (Groww_internship) or from inside the backend directory.
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import api_router
from backend.routes.agent_routes import chat_stream_route
from backend.config.mongodb import MongoDBManager
from backend.config.redis import RedisConnectionManager
from backend.config.chat_model import ChatModelManager
from backend.agent.agent_graph import GrowwAgentGraph


# =====================================================================
# Lifespan Event Handler (Startup & Shutdown)
# =====================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager that initializes and verifies Database, Redis,
    LLM, and LangGraph Agent instances during server startup.
    """
    print("=" * 60)
    print("[Startup] Initializing Groww GenZ Copilot Backend Services...")
    print("=" * 60)

    # 1. Warm-up and test MongoDB Atlas connection
    try:
        db = MongoDBManager.get_instance().get_database()
        await db.command("ping")
        print("[Startup] [OK] MongoDB Atlas: Connection verified & database ready.")
    except Exception as e:
        print(f"[Startup] [WARN] MongoDB Atlas: Initialization warning: {e}")

    # 2. Warm-up and test Redis cache connection
    try:
        redis_mgr = RedisConnectionManager.get_instance()
        if redis_mgr.ping():
            print("[Startup] [OK] Redis Session Store: Connection verified & cache ready.")
        else:
            print("[Startup] [WARN] Redis Session Store: Ping test failed or not responding.")
    except Exception as e:
        print(f"[Startup] [WARN] Redis Session Store: Initialization warning: {e}")

    # 3. Warm-up and initialize OpenRouter Chat Model
    try:
        chat_model = ChatModelManager.get_instance().get_chat_model()
        model_name = getattr(chat_model, "model_name", None) or os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat")
        print(f"[Startup] [OK] OpenRouter LLM: Chat model loaded ({model_name}).")
    except Exception as e:
        print(f"[Startup] [WARN] OpenRouter LLM: Initialization warning: {e}")

    # 4. Warm-up Agent Graph Orchestrator
    try:
        _ = GrowwAgentGraph()
        print("[Startup] [OK] LangGraph Agent: Specialized agents and routes compiled.")
    except Exception as e:
        print(f"[Startup] [WARN] LangGraph Agent: Initialization warning: {e}")

    print("=" * 60)
    print("[Startup] [READY] All Core Services Initialized. Server Ready!")
    print("=" * 60)

    yield

    # Clean shutdown
    print("\n[Shutdown] Closing connection pools...")
    try:
        client = MongoDBManager.get_instance().get_client()
        if client:
            client.close()
            print("[Shutdown] [OK] MongoDB connection closed.")
    except Exception:
        pass
    print("[Shutdown] [DONE] Backend shutdown complete.")


# =====================================================================
# FastAPI Application Initialization
# =====================================================================
app = FastAPI(
    title="Groww GenZ Copilot API",
    description="Backend service with clean Routes & Controllers architecture for Users, Stocks, Goals, and AI Agent.",
    version="1.0.0",
    lifespan=lifespan
)

# Open CORS configuration to allow all incoming traffic.
# Note: allow_credentials must be False when using wildcards ("*").
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Allows all domains
    allow_credentials=False,  # Required by browsers when origin is "*"
    allow_methods=["*"],      # Allows all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],      # Allows all headers
)

# =====================================================================
# Mount Central API Router (/api/users, /api/stocks, /api/goals, /api/agent)
# =====================================================================
app.include_router(api_router)

# Backward compatibility route for frontend SSE clients (/api/chat/stream -> agent stream)
app.add_api_route("/api/chat/stream", chat_stream_route, methods=["POST"])


# =====================================================================
# Health Check Endpoint
# =====================================================================
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Groww GenZ Backend",
        "version": "1.0.0",
        "routes": ["users", "stocks", "goals", "agent"]
    }


if __name__ == "__main__":
    # Works whether executed from root (Groww_internship) or from within backend folder
    app_target = "main:app" if Path.cwd().name == "backend" else "backend.main:app"
    uvicorn.run(app_target, host="0.0.0.0", port=8000, reload=True)
