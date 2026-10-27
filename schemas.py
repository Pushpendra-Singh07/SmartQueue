from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from models import Priority, QueueStatus


class PatientOut(BaseModel):
    id: int
    name: str
    age: int
    gender: str
    contact: Optional[str] = None

    model_config = {"from_attributes": True}


class QueueEntryOut(BaseModel):
    id: int
    token_no: str
    patient: PatientOut
    doctor_id: int
    priority: Priority
    status: QueueStatus
    check_in_time: datetime

    model_config = {"from_attributes": True}
