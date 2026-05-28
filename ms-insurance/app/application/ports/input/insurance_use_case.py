from abc import ABC, abstractmethod


class InsuranceUseCase(ABC):

    @abstractmethod
    def validate_coverage(self, patient_id: str, procedure_code: str) -> dict:
        pass

    @abstractmethod
    def seed_policies(self) -> dict:
        pass
