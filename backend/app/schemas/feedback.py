from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FeedbackCreate(BaseModel):
    """Trainee feedback (needs a rating) or a lead correction (needs the correction text).

    The two kinds are kept apart on purpose: a lead correction has no rating and
    no trainee comment, and trainee feedback cannot carry a lead correction.
    """

    question_id: int
    feedback_type: Literal["trainee_feedback", "lead_correction"] = "trainee_feedback"
    rating: int | None = Field(default=None, ge=1, le=5)
    trainee_comment: str | None = Field(default=None, max_length=2000)
    lead_correction: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def check_type_rules(self) -> Self:
        if self.feedback_type == "trainee_feedback":
            if self.rating is None:
                raise ValueError("a rating (1-5) is required for trainee feedback")
            if self.lead_correction:
                raise ValueError("trainee feedback cannot include a lead correction")
        else:
            if not (self.lead_correction and self.lead_correction.strip()):
                raise ValueError("lead_correction text is required for a lead correction")
            if self.rating is not None or self.trainee_comment:
                raise ValueError("a lead correction cannot include a rating or trainee comment")
        return self


class FeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question_id: int
    feedback_type: str
    rating: int | None
    trainee_comment: str | None
    lead_correction: str | None
    created_at: datetime
