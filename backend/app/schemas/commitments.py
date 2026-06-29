from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any
from datetime import datetime
import uuid

class TaskSchema(BaseModel):
    id: uuid.UUID
    title: str
    status: str
    estimated_minutes: int
    actual_minutes: int
    sequence_order: int
    next_action: Optional[str] = None
    done_condition: Optional[str] = None

class FocusBlockSchema(BaseModel):
    id: uuid.UUID
    title: str
    start_at: datetime
    end_at: datetime
    block_type: str
    status: str
    
class ReflectionSchema(BaseModel):
    id: uuid.UUID
    planned_minutes: int
    actual_minutes: int
    completion_status: str
    energy_level: int
    blocker_reason: Optional[str] = None
    quality_confidence: Optional[str] = None
    notes: Optional[str] = None

class NormalizedTimeSpineStage(BaseModel):
    key: str
    label: str
    order: int
    status: str
    timestamp: Optional[str] = None
    risk_level: Optional[str] = None
    explanation: Optional[str] = None

class CommitmentDetailResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    type: str
    status: str
    deadline_at: Optional[datetime] = None
    start_before_at: Optional[datetime] = None
    estimated_minutes: int
    actual_minutes: int
    importance: int
    flexibility: int
    progress_percent: float
    risk_score: float
    risk_level: str
    confidence_score: float
    
    tasks: List[TaskSchema] = []
    time_spine_stages: List[NormalizedTimeSpineStage] = []
    focus_blocks: List[FocusBlockSchema] = []
    reflections: List[ReflectionSchema] = []
    current_stage: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
