from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.model.appointment import Appointment


class AppointmentRepositoryPort(ABC):

    @abstractmethod
    def save(self, appointment: Appointment) -> Appointment:
        pass

    @abstractmethod
    def get_by_id(self, appointment_id: int) -> Optional[Appointment]:
        pass

    @abstractmethod
    def list_by_patient(self, patient_id: str) -> List[Appointment]:
        pass

    @abstractmethod
    def delete(self, appointment_id: int) -> None:
        pass
