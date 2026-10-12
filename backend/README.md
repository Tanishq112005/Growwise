# Groww GenZ Backend Service

Python FastAPI backend designed for low latency, zero-jargon translation, and SEBI compliance guardrails.

## Quickstart

All imports use the `backend.` package, so **run everything from the repository root** (the folder that contains `backend/` and `frontend/`), not from inside `backend/`.

1. Create a virtual environment (repo root):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. Create `backend/.env` with:
   ```
   OPENROUTER_API_KEY=...
   MONGODB_URI=mongodb://localhost:27017
   MONGODB_DB_NAME=growwise_db
   TWELVE_DATA_API_KEY=...
   TAVILY_API_KEY=...
   CORS_ORIGINS=http://localhost:5173
   ```

4. Run the development server (repo root):
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```

5. Health check:
   - GET `http://localhost:8000/api/health`

Chat memory notes: conversation memory is in-process (`MemorySaver`, keyed by `user_id:chat_id`);
finished turns are persisted to MongoDB.
