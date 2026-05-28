from abc import ABC, abstractmethod
from typing import Optional


class PolicyRepositoryPort(ABC):

    @abstractmethod
    def find_policy(self, patient_id: str, procedure_code: str) -> Optional[object]:
        pass

    @abstractmethod
    def save_policy(self, patient_id: str, procedure_code: str,
                    covered: bool, rejection_code: str = None) -> None:
        pass
