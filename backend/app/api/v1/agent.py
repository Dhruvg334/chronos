from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio

router = APIRouter()

@router.get("/proposed")
async def get_proposed_actions():
    return []

@router.post("/proposed/{action_id}/approve")
async def approve_proposed_action(action_id: str):
    return {"message": f"Mock approved action {action_id}"}

@router.post("/proposed/{action_id}/reject")
async def reject_proposed_action(action_id: str):
    return {"message": f"Mock rejected action {action_id}"}

@router.get("/runs/{run_id}/trace")
async def get_agent_trace_stream(run_id: str):
    # Mock SSE stream for agent trace
    async def event_generator():
        yield "data: {\"step_name\": \"Intake\", \"status\": \"completed\", \"explanation\": \"Scanned inputs (Mock)\"}\n\n"
        await asyncio.sleep(1)
        yield "data: {\"step_name\": \"Done\", \"status\": \"completed\", \"explanation\": \"Ready (Mock)\"}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")
