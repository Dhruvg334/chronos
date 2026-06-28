from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from datetime import datetime, timezone
import uuid
import json

from app.schemas.intake import (
    BrainDumpRequest,
    IntakeResponse,
    ExtractedCommitment,
    ClarifyingQuestion,
    ApproveCommitmentsRequest,
    ApproveCommitmentsResponse
)
from app.api.dependencies import get_current_user
from app.services.gemini_service import gemini_service
from app.services.trace_service import AgentTraceLogger, create_agent_run, update_agent_run
from app.services.risk_service import calculate_initial_risk
from app.core.database import supabase_client

router = APIRouter(prefix="/api/v1/ai/intake", tags=["ai", "intake"])

class IntakePromptResponse(IntakeResponse):
    pass  # We use the generic IntakeResponse schema

@router.post("", response_model=IntakeResponse)
async def process_intake(request: BrainDumpRequest, user_id: str = Depends(get_current_user)):
    # 1. Create agent run
    agent_run_id = create_agent_run(user_id, "intake", {"text": request.text})
    if not agent_run_id:
        raise HTTPException(status_code=500, detail="Database not initialized.")
        
    trace_logger = AgentTraceLogger(user_id, agent_run_id)
    trace_logger.log("intake_received")
    
    # 2. Extract using Gemini
    prompt = f"""
    The user has provided a brain dump of things they need to do:
    "{request.text}"
    
    Extract all commitments, tasks, and potential clarifying questions.
    """
    
    try:
        # Request is simple enough that we try fast model first
        class ModelOutput(IntakeResponse):
            pass # We just want the drafts and questions
            
        result = gemini_service.extract_structured(prompt, IntakeResponse, require_reasoning=False, trace_logger=trace_logger)
        
        # Override the agent_run_id to match the database one
        result.agent_run_id = uuid.UUID(agent_run_id)
        
        trace_logger.log("drafts_prepared", {"count": len(result.drafts)})
        update_agent_run(agent_run_id, "completed")
        
        return result
    except Exception as e:
        trace_logger.log("extraction_failed", {"error": str(e)})
        update_agent_run(agent_run_id, "failed")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/approve", response_model=ApproveCommitmentsResponse)
async def approve_intake(request: ApproveCommitmentsRequest, user_id: str = Depends(get_current_user)):
    if not request.approved_drafts:
        raise HTTPException(status_code=400, detail="No approved drafts provided.")
        
    # Link trace events to the original intake agent_run, since approval is a continuation of that process
    agent_run_id = str(request.agent_run_id)
    trace_logger = AgentTraceLogger(user_id, agent_run_id)
    trace_logger.log("approval_received", {"count": len(request.approved_drafts)})
    
    now = datetime.now(timezone.utc)
    commitments_inserted = 0
    
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database not initialized.")
        
    try:
        for draft in request.approved_drafts:
            # Calculate Risk
            risk_score, risk_level, warnings = calculate_initial_risk(
                current_time=now,
                deadline_at=datetime.fromisoformat(draft.deadline_at.replace('Z', '+00:00')) if draft.deadline_at else None,
                estimated_minutes=draft.estimated_minutes,
                progress_percent=0.0,
                importance=draft.importance,
                flexibility=draft.flexibility,
                confidence_score=draft.confidence_score,
                start_before_at=datetime.fromisoformat(draft.start_before_at.replace('Z', '+00:00')) if draft.start_before_at else None
            )
            
            # Prepare commitment data
            commitment_id = str(uuid.uuid4())
            comm_data = {
                "id": commitment_id,
                "user_id": user_id,
                "title": draft.title,
                "status": "active",
                "commitment_type": draft.type,
                "deadline_at": draft.deadline_at,
                "estimated_effort_minutes": draft.estimated_minutes,
                "importance": draft.importance,
                "flexibility": draft.flexibility,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "done_condition": draft.done_condition,
                "next_action": draft.next_action,
                "ai_confidence_score": draft.confidence_score
            }
            supabase_client.table("commitments").insert(comm_data).execute()
            trace_logger.log("commitments_persisted", {"id": commitment_id, "title": draft.title})
            trace_logger.log("risk_initialized", {"id": commitment_id, "risk_level": risk_level})
            
            # Insert tasks
            if draft.tasks:
                task_rows = []
                for idx, t in enumerate(draft.tasks):
                    task_rows.append({
                        "id": str(uuid.uuid4()),
                        "commitment_id": commitment_id,
                        "title": t.title,
                        "status": "pending",
                        "estimated_minutes": t.estimated_minutes,
                        "order_index": idx
                    })
                supabase_client.table("tasks").insert(task_rows).execute()
                trace_logger.log("tasks_created", {"commitment_id": commitment_id, "count": len(task_rows)})
                
            # Initialize Basic Time Spine
            # We create a simple spine based on the type
            checkpoints = [
                {"id": "capture", "status": "completed", "label": "Captured"},
                {"id": "next_action", "status": "pending", "label": "Next Action"}
            ]
            
            if draft.type in ["project", "milestone"]:
                checkpoints.extend([
                    {"id": "buffer", "status": "pending", "label": "Buffer Zone"},
                    {"id": "final_deadline", "status": "pending", "label": "Final Deadline"}
                ])
                
            spine_data = {
                "id": str(uuid.uuid4()),
                "commitment_id": commitment_id,
                "checkpoints_json": checkpoints,
                "current_checkpoint_id": "next_action"
            }
            supabase_client.table("time_spines").insert(spine_data).execute()
            trace_logger.log("time_spines_created", {"commitment_id": commitment_id})
            
            commitments_inserted += 1
            
        trace_logger.log("approval_completed")
        update_agent_run(agent_run_id, "completed")
        
        return ApproveCommitmentsResponse(
            status="success",
            count=commitments_inserted,
            message=f"Successfully approved {commitments_inserted} commitments."
        )
    except Exception as e:
        trace_logger.log("approval_failed", {"error": str(e)})
        update_agent_run(agent_run_id, "failed")
        raise HTTPException(status_code=500, detail=f"Database insert failed: {str(e)}")
