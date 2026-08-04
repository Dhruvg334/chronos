from pydantic import BaseModel
from app.workflows.approval import RecommendationFirstApprovalPolicy
from app.workflows.tools import PermissionClass, ToolSpec

class Args(BaseModel): value: str = "x"
class Result(BaseModel): ok: bool
async def handler(args): return Result(ok=True)
def tool(permission): return ToolSpec("t","test",Args,Result,permission,1,True,"permission",handler,required_scopes=("read",),data_accessed=("context",),approval_required=permission not in {PermissionClass.READ_INTERNAL,PermissionClass.READ_EXTERNAL},idempotency_behavior="keyed",rollback_capability="proposal_only")

def test_central_permission_classes_are_enforced():
    policy = RecommendationFirstApprovalPolicy()
    assert policy.evaluate(tool(PermissionClass.READ_EXTERNAL)).allowed
    assert policy.evaluate(tool(PermissionClass.PROPOSE_EXTERNAL_WRITE)).allowed
    assert policy.evaluate(tool(PermissionClass.PROPOSE_EXTERNAL_WRITE)).requires_user_approval
    assert not policy.evaluate(tool(PermissionClass.APPROVED_EXTERNAL_WRITE)).allowed
    assert policy.evaluate(tool(PermissionClass.APPROVED_EXTERNAL_WRITE), user_approved=True).allowed
    assert not policy.evaluate(tool(PermissionClass.PROHIBITED)).allowed
