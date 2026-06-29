import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def parse_iso(dt_str: str) -> datetime:
    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))

def rank_commitments(commitments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Rank commitments deterministically.
    Higher score = higher priority for scheduling.
    """
    now = datetime.now(timezone.utc)
    ranked = []
    for c in commitments:
        if c.get("status") != "active" and c.get("status") != "at_risk":
            continue
            
        risk_score = c.get("risk_score", 0)
        effort_remaining = c.get("estimated_minutes", 0) - c.get("actual_minutes", 0)
        if effort_remaining <= 0:
            continue
            
        deadline = parse_iso(c["deadline_at"])
        hours_until = (deadline - now).total_seconds() / 3600
        if hours_until <= 0:
            hours_until = 0.1 # avoid division by zero
            
        # Basic heuristic: risk * effort / time
        priority = (risk_score * effort_remaining) / (hours_until * 24)
        
        c["_priority"] = priority
        ranked.append(c)
        
    return sorted(ranked, key=lambda x: x["_priority"], reverse=True)

def detect_overlaps(
    start_at: datetime, 
    end_at: datetime, 
    existing_blocks: List[Dict[str, Any]], 
    busy_windows: List[Dict[str, Any]]
) -> bool:
    """Check if the proposed time overlaps with existing blocks or calendar busy time."""
    
    # Check internal focus blocks
    for block in existing_blocks:
        b_start = parse_iso(block["start_at"])
        b_end = parse_iso(block["end_at"])
        if start_at < b_end and end_at > b_start:
            return True
            
    # Check external busy windows
    for busy in busy_windows:
        busy_start = parse_iso(busy["start"])
        busy_end = parse_iso(busy["end"])
        if start_at < busy_end and end_at > busy_start:
            return True
            
    return False

def derive_proposal_reason(commitment: Dict[str, Any]) -> str:
    """Generate a deterministic reason for the proposed block."""
    risk_level = commitment.get("risk_level", "stable")
    if risk_level == "rescue_required":
        return f"CRITICAL: Commitment '{commitment['title']}' is failing. Rescue block required immediately."
    elif risk_level == "at_risk":
        return f"WARNING: Commitment '{commitment['title']}' is falling behind. Proposing block to recover progress."
    else:
        return f"Proposing proactive block for '{commitment['title']}' to maintain steady progress."

def validate_candidate_block(block: Dict[str, Any], commitments: List[Dict[str, Any]]) -> bool:
    """Ensure the block meets logical constraints (duration bounds, existence of commitment)."""
    duration = block.get("duration_minutes", 0)
    if duration < 15 or duration > 240:
        return False
        
    cid = block.get("commitment_id")
    if not any(c["id"] == cid for c in commitments):
        return False
        
    start_at = parse_iso(block["start_at"])
    end_at = parse_iso(block["end_at"])
    if end_at <= start_at:
        return False
        
    return True

def generate_candidate_blocks(
    commitments: List[Dict[str, Any]],
    capacity_slots: List[Dict[str, Any]],
    existing_blocks: List[Dict[str, Any]],
    busy_windows: List[Dict[str, Any]],
    source: str
) -> List[Dict[str, Any]]:
    """
    Greedy approach to map high priority commitments to available capacity slots.
    capacity_slots: [{"start": "...", "end": "..."}] representing free time.
    """
    proposals = []
    ranked_commitments = rank_commitments(commitments)
    
    for c in ranked_commitments:
        effort_needed = c.get("estimated_minutes", 0) - c.get("actual_minutes", 0)
        if effort_needed <= 0:
            continue
            
        # Try to find a slot
        for slot in capacity_slots:
            slot_start = parse_iso(slot["start"])
            slot_end = parse_iso(slot["end"])
            
            # Use chunks of up to 90 mins (or effort needed, whichever is smaller)
            block_duration = min(effort_needed, 90)
            
            # Does the slot fit the block?
            if (slot_end - slot_start).total_seconds() / 60 >= block_duration:
                proposed_start = slot_start
                proposed_end = proposed_start + timedelta(minutes=block_duration)
                
                # Check overlaps
                if not detect_overlaps(proposed_start, proposed_end, existing_blocks, busy_windows):
                    # We can propose this!
                    proposal = {
                        "action_type": "create_focus_block",
                        "commitment_id": c["id"],
                        "title": f"Focus: {c['title']}",
                        "start_at": proposed_start.isoformat(),
                        "end_at": proposed_end.isoformat(),
                        "duration_minutes": block_duration,
                        "risk_level": c.get("risk_level", "stable"),
                        "reason": derive_proposal_reason(c),
                        "confidence_score": min(95, int(c.get("_priority", 50) * 10)),
                        "capacity_source": source,
                        "validation_status": "valid"
                    }
                    
                    if validate_candidate_block(proposal, commitments):
                        proposals.append(proposal)
                        # Reduce effort needed and update slot start so we don't reuse the exact time
                        effort_needed -= block_duration
                        slot["start"] = proposed_end.isoformat()
                        
                        # Add a 15 min buffer to the slot to avoid back-to-back
                        buffer_end = proposed_end + timedelta(minutes=15)
                        if buffer_end < slot_end:
                            slot["start"] = buffer_end.isoformat()
                        
                        if effort_needed <= 0:
                            break
                            
    return proposals
