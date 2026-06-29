from typing import Any, Dict

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.api.v1.command import load_judge_demo

router = APIRouter()


@router.post("/load")
def load_demo(user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Canonical judge-demo loader route used by the frontend."""
    return load_judge_demo(user_id)
