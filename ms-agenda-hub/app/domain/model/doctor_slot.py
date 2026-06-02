from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from app.domain.model.value_objects import SlotStatus


@dataclass
class DoctorSlot:
    id:            Optional[int]
    doctor_id:     int
    doctor_name:   str
    specialty:     str
    slot_datetime: datetime
    status:        SlotStatus = SlotStatus.AVAILABLE
