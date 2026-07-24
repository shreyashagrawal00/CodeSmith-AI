import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.api.websocket import ws_router
from app.database.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Creates the SQLite tables (backend/codesmith.db) if they don't exist
    # yet. Safe to call every time the app starts.
    init_db()
    yield


app = FastAPI(
    title="CodeSmith AI",
    description="Autonomous Multi-Agent Software Engineering Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS – allow the React frontend.
# In production set ALLOWED_ORIGINS as a comma-separated list of URLs, e.g.:
#   https://codesmith-ai.vercel.app,https://your-custom-domain.com
_default_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "http://[::1]:5173",
    "http://[::1]:3000",
]
_extra_origins = [
    o.strip()
    for o in os.environ.get("ALLOWED_ORIGINS", "").split(",")
    if o.strip()
]
_allow_origins = _default_origins + _extra_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST routes
app.include_router(router, prefix="/api/v1", tags=["Generation"])

# WebSocket route
app.include_router(ws_router, tags=["WebSocket"])


@app.get("/")
def health():
    return {"message": "CodeSmith AI is running 🚀", "version": "1.0.0"}