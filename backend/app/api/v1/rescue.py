from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header

from app.api.dependencies import get_current_user, get_repositories
from app.core.errors import ChronosError, ErrorCode
from app.repositories.protocols import RepositorySet
from app.services.core_journey import rank_commitments

router = APIRouter()


@router.get("/candidates")
def get_rescue_candidates(user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)) -> dict[str, Any]:
    rows = rank_commitments(repositories.commitments.list_for_user(user_id))
    return {"candidates": [{**row, "_rescue_reason": "The current risk and remaining work need a more credible plan."} for row in rows if row.get("risk_level") in {"at_risk", "critical", "rescue_required"}]}


@router.post("/{commitment_id}/plan")
def generate_rescue_plan(commitment_id: str, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)) -> dict[str, Any]:
    commitment = repositories.commitments.get_for_user(user_id, commitment_id)
    if not commitment:
        raise ChronosError(ErrorCode.VALIDATION, "Commitment not found.")
    workflow_id = str(uuid.uuid4())
    run_id = repositories.traces.create_run(user_id, "recovery", {"commitment_id": commitment_id}, workflow_id=workflow_id)
    payload = {"rescue_action_type": "compress_scope", "commitment_id": commitment_id, "title": f"Reduce the next scope for {commitment['title']}", "suggestion": "Define the smallest acceptable next outcome before moving lower-priority work."}
    proposal = repositories.planning.create_proposal(user_id, {"id": str(uuid.uuid4()), "agent_run_id": run_id, "action_type": "commitment_rescue", "status": "pending", "payload_json": payload, "explanation": "This is a recommendation. No plan data changes until you approve it."})
    repositories.traces.append(user_id, run_id, {"step_name": "recovery_proposed", "status": "succeeded", "explanation": "Prepared a recovery recommendation.", "payload_json": {"commitment_id": commitment_id}})
    repositories.traces.complete_run(user_id, run_id, {"proposal_count": 1})
    return {"status": "plan_generated", "proposals": [proposal]}


@router.get("/plans")
def get_rescue_plans(user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)) -> dict[str, Any]:
    return {"proposals": [row for row in repositories.planning.list_pending(user_id) if row.get("action_type") == "commitment_rescue"]}


def _pending(repositories: RepositorySet, user_id: str, proposal_id: str) -> dict[str, Any]:
    proposal = repositories.planning.get_proposal(user_id, proposal_id)
    if not proposal or proposal.get("action_type") != "commitment_rescue":
        raise ChronosError(ErrorCode.VALIDATION, "Recovery proposal not found.")
    if proposal.get("status") != "pending":
        raise ChronosError(ErrorCode.CONFLICT, "This recovery proposal is no longer pending.")
    return proposal


@router.post("/proposals/{proposal_id}/approve")
def approve_rescue_proposal(proposal_id: str, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)) -> dict[str, Any]:
    proposal = _pending(repositories, user_id, proposal_id)
    payload = proposal.get("payload_json") or {}
    focus_block_id = str(uuid.uuid4()) if payload.get("rescue_action_type") == "create_rescue_focus_block" else None
    return repositories.planning.approve_recovery(user_id, proposal_id, idempotency_key or f"recovery-{proposal_id}", focus_block_id)


@router.post("/proposals/{proposal_id}/reject")
def reject_rescue_proposal(proposal_id: str, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)) -> dict[str, Any]:
    _pending(repositories, user_id, proposal_id)
    repositories.planning.update_proposal(user_id, proposal_id, {"status": "rejected"})
    return {"status": "rejected"}
