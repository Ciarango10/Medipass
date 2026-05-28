from abc import ABC, abstractmethod


class EHRLogUseCase(ABC):

    @abstractmethod
    def log_appointment(self, event: dict) -> dict:
        """Persiste el resumen de una cita confirmada en el HCD."""
        pass

    @abstractmethod
    def get_history_by_patient(self, patient_id: str) -> list:
        pass
