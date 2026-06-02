from abc import ABC, abstractmethod
from typing import List, Optional


class AppointmentUseCase(ABC):

    @abstractmethod
    def schedule_appointment(self, patient_id: str, patient_name: str,
                             doctor_id: int, slot_id: int, procedure_code: str) -> dict:
        pass

    @abstractmethod
    def get_appointment(self, appointment_id: int) -> dict:
        pass

    @abstractmethod
    def list_appointments_by_patient(self, patient_id: str) -> List[dict]:
        pass

    @abstractmethod
    def cancel_appointment(self, appointment_id: int) -> dict:
        pass


class DoctorSlotUseCase(ABC):

    @abstractmethod
    def create_slot(self, doctor_id: int, doctor_name: str,
                    specialty: str, slot_datetime: str) -> dict:
        pass

    @abstractmethod
    def list_available_slots(self, specialty: Optional[str] = None) -> List[dict]:
        pass
