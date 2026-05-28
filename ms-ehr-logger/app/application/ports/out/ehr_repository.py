from abc import ABC, abstractmethod
from typing import List


class EHRRepositoryPort(ABC):

    @abstractmethod
    def save(self, record) -> object:
        pass

    @abstractmethod
    def find_by_patient(self, patient_id: str) -> List[object]:
        pass
