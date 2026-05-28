from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class EHRRecord:
    """Documento del Historial Clínico Digital.
    Schema flexible: diferentes especialidades añaden campos propios."""

    appointment_id:  int
    patient_id:      str
    patient_name:    str
    doctor_id:       int
    doctor_name:     str
    specialty:       str
    procedure_code:  str
    coverage_status: str
    slot_datetime:   str
    confirmed_at:    datetime = field(default_factory=datetime.now)
    notes:           Optional[str] = None
    mongo_id:        Optional[str] = None  # _id de MongoDB tras persistir

    def to_document(self) -> dict:
        """Convierte el registro a documento MongoDB."""
        return {
            "appointment_id":  self.appointment_id,
            "patient_id":      self.patient_id,
            "patient_name":    self.patient_name,
            "doctor_id":       self.doctor_id,
            "doctor_name":     self.doctor_name,
            "specialty":       self.specialty,
            "procedure_code":  self.procedure_code,
            "coverage_status": self.coverage_status,
            "slot_datetime":   self.slot_datetime,
            "confirmed_at":    str(self.confirmed_at),
            "notes":           self.notes,
        }

    @classmethod
    def from_event(cls, event: dict) -> "EHRRecord":
        """Factory: construye un EHRRecord a partir del evento de RabbitMQ."""
        return cls(
            appointment_id  = event["appointment_id"],
            patient_id      = event["patient_id"],
            patient_name    = event["patient_name"],
            doctor_id       = event["doctor_id"],
            doctor_name     = event.get("doctor_name", ""),
            specialty       = event.get("specialty", ""),
            procedure_code  = event["procedure_code"],
            coverage_status = event.get("coverage_status", "COVERED"),
            slot_datetime   = event.get("slot_datetime", ""),
        )
