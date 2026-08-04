from __future__ import annotations

from dataclasses import dataclass

from app.workflows.tools import PermissionClass, ToolSpec


@dataclass(frozen=True)
class ApprovalDecision:
    allowed: bool
    requires_user_approval: bool
    reason: str


class RecommendationFirstApprovalPolicy:
    def evaluate(self, tool: ToolSpec, *, user_approved: bool = False, internal_write_enabled: bool = False) -> ApprovalDecision:
        if tool.permission == PermissionClass.PROHIBITED:
            return ApprovalDecision(False, False, "This capability is prohibited.")
        if tool.permission == PermissionClass.APPROVED_EXTERNAL_WRITE:
            return ApprovalDecision(user_approved, True, "External changes require explicit approval.")
        if tool.permission == PermissionClass.APPROVED_INTERNAL_WRITE:
            allowed = user_approved or (internal_write_enabled and tool.idempotent)
            return ApprovalDecision(allowed, not allowed, "Internal changes require approval unless reversible automation is enabled.")
        if tool.permission in {PermissionClass.PROPOSE_INTERNAL_WRITE, PermissionClass.PROPOSE_EXTERNAL_WRITE}:
            return ApprovalDecision(True, True, "This tool may create a proposal but cannot execute the proposed change.")
        return ApprovalDecision(True, False, "Read-only tools are allowed within workflow bounds.")
