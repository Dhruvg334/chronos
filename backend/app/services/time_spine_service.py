from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.core.database import supabase_client
import logging

logger = logging.getLogger(__name__)

def normalize_spine_json(spine_json: List[Dict[str, Any]], current_stage: str, risk_level: str) -> List[Dict[str, Any]]:
    """
    Normalizes the raw spine_json into a frontend-friendly shape.
    """
    normalized = []
    found_current = False
    
    for i, stage in enumerate(spine_json):
        stage_id = stage.get("id")
        
        # Determine status relative to current_stage
        status = stage.get("status", "pending")
        if status == "pending" and not found_current:
            if stage_id == current_stage:
                status = "active"
                found_current = True
            else:
                status = "completed"
        elif status == "pending" and found_current:
            status = "pending"
        elif stage_id == current_stage:
            status = "active"
            found_current = True
            
        normalized.append({
            "key": stage_id,
            "label": stage.get("label", stage_id),
            "order": i,
            "status": status,
            "timestamp": stage.get("timestamp"),
            "risk_level": risk_level if status == "active" else None,
            "explanation": stage.get("explanation")
        })
    return normalized


def get_time_spine_view(commitment_id: str, user_id: str) -> Dict[str, Any]:
    """
    Fetches the time spine and commitment risk, returning a normalized view.
    """
    if not supabase_client:
        return {"stages": [], "current_stage": None}

    # Fetch time spine
    spine_res = supabase_client.table("time_spines").select("*").eq("commitment_id", commitment_id).eq("user_id", user_id).single().execute()
    if not spine_res.data:
        return {"stages": [], "current_stage": None}

    # Fetch commitment risk level
    comm_res = supabase_client.table("commitments").select("risk_level").eq("id", commitment_id).single().execute()
    risk_level = comm_res.data.get("risk_level") if comm_res.data else "stable"

    spine_json = spine_res.data.get("spine_json", [])
    current_stage = spine_res.data.get("current_stage")

    normalized = normalize_spine_json(spine_json, current_stage, risk_level)
    
    return {
        "stages": normalized,
        "current_stage": current_stage
    }


def advance_time_spine_stage(commitment_id: str, user_id: str, event_type: str = "progress") -> None:
    """
    Advances the current_stage based on events like progress or reflection.
    """
    if not supabase_client:
        return
        
    spine_res = supabase_client.table("time_spines").select("*").eq("commitment_id", commitment_id).eq("user_id", user_id).single().execute()
    if not spine_res.data:
        return
        
    spine = spine_res.data
    spine_json = spine.get("spine_json", [])
    current_stage = spine.get("current_stage")
    
    # Simple progression logic: just find current_stage and move to the next if it exists
    next_stage = current_stage
    found = False
    
    for i, stage in enumerate(spine_json):
        if stage.get("id") == current_stage:
            found = True
            # Check if there is a next stage
            if i + 1 < len(spine_json):
                next_stage = spine_json[i+1].get("id")
                
                # Mark current stage as completed with a timestamp
                stage["status"] = "completed"
                stage["timestamp"] = datetime.now(timezone.utc).isoformat()
            break
            
    if found and next_stage != current_stage:
        supabase_client.table("time_spines").update({
            "current_stage": next_stage,
            "spine_json": spine_json
        }).eq("id", spine["id"]).execute()
        
        logger.info(f"Advanced time spine for commitment {commitment_id} to stage {next_stage}")
