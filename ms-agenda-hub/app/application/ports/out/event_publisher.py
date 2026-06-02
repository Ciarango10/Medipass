from abc import ABC, abstractmethod


class EventPublisherPort(ABC):

    @abstractmethod
    def publish(self, queue: str, message: dict) -> None:
        pass
