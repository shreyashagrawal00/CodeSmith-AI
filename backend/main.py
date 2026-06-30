from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.api.websocket import ws_router

app = FastAPI(
    title="CodeSmith AI",
    description="Autonomous Multi-Agent Software Engineering Platform",
    version="1.0.0",
)

# CORS – allow the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
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
