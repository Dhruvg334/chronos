from typing import Any, Literal
from pydantic import BaseModel, Field


class IntegrationProposalRequest(BaseModel):
    item_id: str
    action_type: Literal["create_task", "create_outcome", "create_event", "create_reference", "link_project"]
    safe_summary: str = Field(min_length=1, max_length=500)
    project_id: str | None = None
    idempotency_key: str = Field(min_length=8, max_length=160)


class ProposalDecisionRequest(BaseModel):
    decision: Literal["rejected", "dismissed"]


class ProposalApprovalRequest(BaseModel):
    action_type: Literal["create_task", "create_outcome", "create_event", "create_reference"]
    project_id: str | None = None


class McpInvocationRequest(BaseModel):
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ResourceSelectionRequest(BaseModel):
    resources: list[str] = Field(max_length=50)
