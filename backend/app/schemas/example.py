from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ExampleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rule_id: int
    input_text: str
    correct_output: str
    explanation: str | None
    created_at: datetime
