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
        if tool.permission == PermissionClass.EXTERNAL_WRITE:
            return ApprovalDecision(user_approved, True, "External changes require explicit approval.")
        if tool.permission == PermissionClass.INTERNAL_WRITE:
            allowed = user_approved or (internal_write_enabled and tool.idempotent)
            return ApprovalDecision(allowed, not allowed, "Internal changes require approval unless reversible automation is enabled.")
        return ApprovalDecision(True, False, "Read-only tools are allowed within workflow bounds.")
