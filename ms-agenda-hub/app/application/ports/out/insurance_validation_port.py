from abc import ABC, abstractmethod
from app.domain.model.insurance_coverage import InsuranceCoverage


class InsuranceValidationPort(ABC):

    @abstractmethod
    def validate_coverage(self, patient_id: str, procedure_code: str) -> InsuranceCoverage:
        pass
