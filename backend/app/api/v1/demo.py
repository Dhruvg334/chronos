from typing import Any, Dict

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.api.v1.command import load_sample_scenario

router = APIRouter()


@router.post("/load")
def load_demo(user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Load an isolated sample scenario into an authenticated workspace."""
    return load_sample_scenario(user_id)
