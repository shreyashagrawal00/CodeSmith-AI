from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from app.services.workflow_service import get_job
import asyncio
import json

ws_router = APIRouter()


@ws_router.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket endpoint that streams job progress updates to the client.
    
    Sends two event types:
    - "progress": an agent completed (coarse-grained, for the agent grid)
    - "live": a granular live_log entry (LLM call, guardrail result, retry, etc.)
    - "done": job finished or failed
    """
    await websocket.accept()
    try:
        last_log_count = 0
        last_live_count = 0

        while True:
            job = get_job(job_id)
            if not job:
                await websocket.send_text(json.dumps({"error": "Job not found"}))
                break

            # ── Coarse-grained agent completion events ─────────────────────
            current_log = job.get("log", [])
            if len(current_log) > last_log_count:
                new_entries = current_log[last_log_count:]
                for entry in new_entries:
                    await websocket.send_text(json.dumps({
                        "type": "progress",
                        "agent": entry.get("agent"),
                        "status": entry.get("status"),
                        "current_agent": job.get("current_agent"),
                        "job_status": job.get("status"),
                    }))
                last_log_count = len(current_log)

            # ── Granular live log events (LLM calls, retries, guardrails) ──
            live_log = job.get("live_log", [])
            if len(live_log) > last_live_count:
                new_live = live_log[last_live_count:]
                for entry in new_live:
                    await websocket.send_text(json.dumps({
                        "type": "live",
                        "agent": entry.get("agent"),
                        "event_type": entry.get("type"),   # info|success|warning|error
                        "message": entry.get("message"),
                        "detail": entry.get("detail", ""),
                    }))
                last_live_count = len(live_log)

            # ── Job completion ─────────────────────────────────────────────
            if job.get("status") in ("completed", "failed"):
                await websocket.send_text(json.dumps({
                    "type": "done",
                    "status": job.get("status"),
                    "error": job.get("error"),
                }))
                break

            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass
