from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from app.domain.model.value_objects import AppointmentStatus


class ProcedureNotCoveredException(Exception):
    def __init__(self, rejection_code: str):
        self.rejection_code = rejection_code
        super().__init__(f"Procedimiento no cubierto: {rejection_code}")


class SlotNotAvailableException(Exception):
    pass


@dataclass
class Appointment:
    id:               Optional[int]
    patient_id:       str
    patient_name:     str
    doctor_id:        int
    slot_id:          int
    procedure_code:   str
    coverage_status:  str
    rejection_code:   Optional[str] = None
    status:           AppointmentStatus = AppointmentStatus.CONFIRMED
    created_at:       Optional[datetime] = None
