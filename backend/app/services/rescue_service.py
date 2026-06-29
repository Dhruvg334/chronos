import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

from app.services.capacity_service import get_layered_capacity
from app.services.gemini_service import gemini_service
from app.services.scheduling_service import parse_iso

logger = logging.getLogger(__name__)

def find_rescue_candidates(commitments: List[Dict[str, Any]], user_id: str, tz_str: str = "UTC") -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc)
    candidates = []
    
    for c in commitments:
        if c.get("status") not in ["active", "at_risk"]:
            continue
            
        risk_level = c.get("risk_level", "stable")
        deadline_str = c.get("deadline_at")
        deadline = parse_iso(deadline_str) if deadline_str else None
        
        is_candidate = False
        reason = ""
        
        # 1. Critical risk level
        if risk_level in ["critical", "rescue_required"]:
            is_candidate = True
            reason = f"Risk level is {risk_level}"
            
        # 2. Overdue and incomplete
        elif deadline and deadline < now:
            is_candidate = True
            reason = "Deadline has passed and commitment is incomplete"
            
        # 3. Insufficient capacity before deadline
        elif deadline:
            effort_remaining = max(c.get("estimated_minutes", 0) - c.get("actual_minutes", 0), 0)
            if effort_remaining > 0:
                cap_data = get_layered_capacity(user_id, deadline, now, tz_str)
                available_minutes = cap_data["available_minutes"]
                
                if available_minutes < effort_remaining:
                    is_candidate = True
                    reason = f"Insufficient capacity ({available_minutes}m available < {effort_remaining}m needed)"
                    
        # 4. Repeated skipped/blocked focus blocks
        # Assumes `focus_blocks` is joined in the commitment data
        if not is_candidate and "focus_blocks" in c:
            skipped_count = sum(1 for b in c["focus_blocks"] if b.get("status") in ["skipped", "blocked"])
            if skipped_count >= 3:
                is_candidate = True
                reason = f"{skipped_count} skipped/blocked focus blocks detected"
                
        # 5. Low progress with high effort remaining (heuristic)
        if not is_candidate:
            progress = c.get("progress_percent", 0)
            effort_remaining = c.get("estimated_minutes", 0) - c.get("actual_minutes", 0)
            if progress < 20 and effort_remaining > 300: # Over 5 hours remaining and < 20% done
                if deadline and (deadline - now).total_seconds() / 3600 < 48: # Less than 48h
                    is_candidate = True
                    reason = "Low progress with high effort remaining close to deadline"
        
        if is_candidate:
            c["_rescue_reason"] = reason
            candidates.append(c)
            
    return candidates

def generate_renegotiation_draft(commitment_title: str, deadline: str) -> str:
    """Generate a draft message. Uses Gemini if available, otherwise deterministic."""
    prompt = (
        f"Write a short, professional message to renegotiate a deadline for '{commitment_title}'. "
        f"The current deadline was {deadline}. State that we need an extension due to unforeseen complexities, "
        f"propose checking in later, and keep it under 3 sentences."
    )
    try:
        # We can just use the generative model directly without schema since we just want text.
        # Wait, GeminiService.extract_structured expects a pydantic model. 
        # For simple text, we'll bypass pydantic or just mock it.
        # Actually, let's just use the raw genai model.
        import google.generativeai as genai
        from app.core.config import settings
        if settings.GEMINI_API_KEY:
            model = genai.GenerativeModel(model_name=settings.GEMINI_MODEL_FAST)
            resp = model.generate_content(prompt)
            return resp.text.strip()
    except Exception as e:
        logger.error(f"Gemini draft generation failed: {e}")
        
    return f"Hi team, I am writing to formally request an extension on '{commitment_title}'. Due to unforeseen complexity, we will not meet the {deadline} deadline. I will provide a new timeline shortly."

def select_rescue_strategy(commitment: Dict[str, Any], user_id: str, tz_str: str = "UTC") -> Dict[str, Any]:
    """
    Decide the rescue strategy based on feasibility score.
    feasibility_score = min(available_minutes / max(effort_remaining_minutes, 1), 1.0)
    """
    now = datetime.now(timezone.utc)
    deadline_str = commitment.get("deadline_at")
    deadline = parse_iso(deadline_str) if deadline_str else (now + timedelta(days=7))
    
    effort_remaining = max(commitment.get("estimated_minutes", 0) - commitment.get("actual_minutes", 0), 1)
    
    if deadline < now:
        # Overdue -> immediate renegotiation or emergency focus
        feasibility_score = 0.1
        available_minutes = 0
        cap_source = "mock"
    else:
        cap_data = get_layered_capacity(user_id, deadline, now, tz_str)
        available_minutes = cap_data["available_minutes"]
        cap_source = cap_data["capacity_source"]
        feasibility_score = min(available_minutes / effort_remaining, 1.0)
        
    # Determine strategy
    if feasibility_score >= 0.85:
        # Recoverable, just schedule emergency blocks
        action_type = "create_rescue_focus_block"
        expected_impact = "High: Should complete within remaining capacity."
        tradeoff = "Consumes most of your remaining free time."
    elif feasibility_score >= 0.50:
        # Need compressed delivery
        action_type = "compress_scope"
        expected_impact = "Medium: Delivers core value, but skips polish."
        tradeoff = "Quality or non-essential features are cut."
    elif feasibility_score >= 0.25:
        # Serious trouble, need deferring tasks and emergency focus
        action_type = "defer_task"
        expected_impact = "Low: Delivers minimum viable product only."
        tradeoff = "Significant scope is pushed to a later date."
    else:
        # Renegotiation likely required
        action_type = "save_renegotiation_draft"
        expected_impact = "Critical: Buys time to avoid complete failure."
        tradeoff = "Requires stakeholder approval and impacts reputation."

    # Construct the JSON payload for the proposal
    payload = {
        "rescue_action_type": action_type,
        "commitment_id": commitment["id"],
        "title": f"Rescue: {commitment['title']}",
        "reason": commitment.get("_rescue_reason", "Risk threshold exceeded."),
        "urgency": "critical",
        "confidence_score": int(feasibility_score * 100),
        "expected_impact": expected_impact,
        "tradeoff": tradeoff,
        "validation_status": "valid"
    }
    
    if action_type == "create_rescue_focus_block":
        # Propose block right now for 90 mins or effort remaining
        duration = min(effort_remaining, 90)
        payload["start_at"] = now.isoformat()
        payload["end_at"] = (now + timedelta(minutes=duration)).isoformat()
        payload["duration_minutes"] = duration
        payload["capacity_source"] = cap_source
        
    elif action_type == "compress_scope":
        payload["minimum_viable_delivery"] = f"Deliver core requirements of '{commitment['title']}' only."
        payload["cut_scope_items"] = ["Polish", "Non-critical edge cases"]
        payload["expected_savings_minutes"] = int(effort_remaining * 0.3) # Save 30%
        
    elif action_type == "defer_task":
        payload["task_ids_to_defer"] = [] # In real app, we'd pick lowest priority tasks
        payload["expected_savings_minutes"] = int(effort_remaining * 0.5) # Save 50%
        
    elif action_type == "save_renegotiation_draft":
        dl = deadline.strftime("%Y-%m-%d") if deadline else "upcoming deadline"
        payload["draft_message"] = generate_renegotiation_draft(commitment["title"], dl)
        payload["suggested_new_deadline"] = (deadline + timedelta(days=7)).isoformat()
        payload["rationale"] = "Insufficient capacity to deliver current scope on time."

    return payload
