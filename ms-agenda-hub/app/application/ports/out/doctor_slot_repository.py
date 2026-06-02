from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.model.doctor_slot import DoctorSlot


class DoctorSlotRepositoryPort(ABC):

    @abstractmethod
    def save(self, slot: DoctorSlot) -> DoctorSlot:
        pass

    @abstractmethod
    def get_by_id(self, slot_id: int) -> Optional[DoctorSlot]:
        pass

    @abstractmethod
    def find_available_slot_for_update(self, slot_id: int) -> Optional[DoctorSlot]:
        pass

    @abstractmethod
    def list_available(self, specialty: Optional[str] = None) -> List[DoctorSlot]:
        pass
