from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
from app.api.dependencies import get_current_user
from app.core.database import supabase_client
from app.services.rescue_service import find_rescue_candidates
from app.services.capacity_service import get_layered_capacity

router = APIRouter()

@router.post("/analyze")
def run_command_analysis(user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database not configured")

    # 1. Load commitments
    res = supabase_client.table("commitments").select("*").eq("user_id", user_id).execute()
    commitments = res.data or []
    
    # 2. Get capacity
    capacity_data = get_layered_capacity(user_id)
    available_minutes = capacity_data.get("available_minutes", 0)
    capacity_source = capacity_data.get("capacity_source", "mock")
    
    # 3. Detect top risks & rescue candidates
    rescue_candidates = find_rescue_candidates(commitments, user_id)
    
    # 4. Determine Time Health (Deterministic Logic)
    time_health = "Stable"
    explanation = "Your plan is currently executable."
    
    # Calculate estimated minutes due soon (next 24 hours)
    now = datetime.now(timezone.utc)
    next_24h = now + timedelta(days=1)
    
    estimated_due_soon = 0
    has_overdue_incomplete = False
    has_compromised_risk = False
    has_watch = False
    
    for c in commitments:
        if c.get("status") in ["completed", "archived"]:
            continue
            
        deadline_str = c.get("deadline_at")
        risk_level = c.get("risk_level", "stable")
        
        if risk_level in ["rescue_required", "critical"]:
            has_compromised_risk = True
        elif risk_level == "watch":
            has_watch = True
            
        if deadline_str:
            deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
            if deadline < now:
                has_overdue_incomplete = True
            if deadline < next_24h:
                has_watch = True
                estimated_due_soon += max(0, c.get("estimated_minutes", 0) - c.get("actual_minutes", 0))

    if has_overdue_incomplete:
        time_health = "Rescue Required"
        explanation = "At least one deadline is slipping and needs intervention."
    elif has_compromised_risk:
        time_health = "Compromised"
        explanation = "Your current workload exceeds available focus capacity."
    elif available_minutes < estimated_due_soon:
        time_health = "Compromised"
        explanation = "Your current workload exceeds available focus capacity."
    elif has_watch:
        time_health = "Watch"
        explanation = "One or more commitments need attention soon."
    
    # 5. Determine next best action
    next_best_action = "No action needed right now."
    if time_health == "Rescue Required":
        next_best_action = "Timeline compromised \u2014 run rescue plan."
    elif rescue_candidates:
        next_best_action = f"ChronOS found {len(rescue_candidates)} actions that need your approval."
    elif commitments:
        next_best_action = "Start with the next safest block."
    
    # 6. Proposal count
    props_res = supabase_client.table("agent_proposed_actions").select("id").eq("user_id", user_id).eq("status", "pending").execute()
    proposal_count = len(props_res.data) if props_res.data else 0

    return {
        "time_health": time_health,
        "time_health_explanation": explanation,
        "capacity_source": capacity_source,
        "available_minutes_today": available_minutes,
        "rescue_candidate_count": len(rescue_candidates),
        "schedule_proposal_count": proposal_count,
        "next_best_action": next_best_action,
        "warnings": []
    }

@router.post("/demo/load")
def load_judge_demo(user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database not configured")

    # 1. Clear existing demo data
    supabase_client.table("commitments").delete().eq("user_id", user_id).like("title", "[DEMO]%").execute()
    
    # 2. Insert new demo data
    now = datetime.now(timezone.utc)
    
    demo_commitments = [
        {
            "user_id": user_id,
            "title": "[DEMO] Final Submission Build",
            "description": "The hackathon submission is due very soon.",
            "type": "hard_deadline",
            "status": "active",
            "deadline_at": (now - timedelta(hours=2)).isoformat(), # Overdue!
            "estimated_minutes": 180,
            "actual_minutes": 0,
            "importance": 5,
            "flexibility": 1,
            "risk_level": "rescue_required",
            "risk_score": 95.0
        },
        {
            "user_id": user_id,
            "title": "[DEMO] Record Demo Video",
            "description": "Need to record the 3-minute pitch.",
            "type": "hard_deadline",
            "status": "active",
            "deadline_at": (now + timedelta(hours=4)).isoformat(), # Due soon
            "estimated_minutes": 60,
            "actual_minutes": 0,
            "importance": 5,
            "flexibility": 2,
            "risk_level": "watch",
            "risk_score": 60.0
        }
    ]
    
    supabase_client.table("commitments").insert(demo_commitments).execute()
    
    return {"status": "Demo scenario loaded successfully."}
