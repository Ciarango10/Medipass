from dataclasses import dataclass
from typing import Optional
from app.domain.model.value_objects import CoverageStatus


@dataclass
class InsuranceCoverage:
    patient_id:     str
    procedure_code: str
    status:         CoverageStatus
    rejection_code: Optional[str] = None
