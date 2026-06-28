from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class BrainDumpRequest(BaseModel):
    text: str = Field(..., description="The raw unstructured text from the user.")

class ClarifyingQuestion(BaseModel):
    question: str = Field(..., description="The clarifying question to ask the user.")
    context: Optional[str] = Field(None, description="Context for why the question is being asked.")

class ExtractedTask(BaseModel):
    title: str = Field(..., description="The title of the task.")
    estimated_minutes: Optional[int] = Field(None, description="Estimated effort in minutes.")

class ExtractedCommitment(BaseModel):
    title: str = Field(..., description="The title of the commitment.")
    type: str = Field(..., description="The type of the commitment (e.g., 'task', 'project', 'event').")
    estimated_minutes: Optional[int] = Field(None, description="Estimated effort in minutes for the whole commitment.")
    deadline_at: Optional[datetime] = Field(None, description="The absolute deadline, if mentioned.")
    start_before_at: Optional[datetime] = Field(None, description="A suggested start time, if applicable.")
    importance: int = Field(3, ge=1, le=5, description="Importance from 1 to 5.")
    flexibility: int = Field(3, ge=1, le=5, description="Flexibility from 1 to 5.")
    done_condition: Optional[str] = Field(None, description="A description of what 'done' looks like.")
    next_action: Optional[str] = Field(None, description="The immediate next actionable step.")
    tasks: List[ExtractedTask] = Field(default_factory=list, description="Subtasks required to complete this commitment.")
    missing_fields: List[str] = Field(default_factory=list, description="List of important fields that are missing or ambiguous.")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0.")

class IntakeResponse(BaseModel):
    agent_run_id: UUID
    drafts: List[ExtractedCommitment]
    questions: List[ClarifyingQuestion]

class CommitmentDraft(ExtractedCommitment):
    # This inherits ExtractedCommitment and can be extended if draft-specific fields are needed.
    pass

class ApproveCommitmentsRequest(BaseModel):
    agent_run_id: UUID
    approved_drafts: List[ExtractedCommitment]

class ApproveCommitmentsResponse(BaseModel):
    status: str
    count: int
    message: str
