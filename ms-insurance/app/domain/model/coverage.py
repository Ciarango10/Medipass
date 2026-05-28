from dataclasses import dataclass
from typing import Optional
from app.domain.model.value_objects import CoverageStatus


@dataclass
class CoverageResult:
    patient_id:     str
    procedure_code: str
    status:         CoverageStatus
    rejection_code: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "patient_id":     self.patient_id,
            "procedure_code": self.procedure_code,
            "status":         self.status.value,
            "rejection_code": self.rejection_code,
        }
