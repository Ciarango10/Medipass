from app.application.ports.input.ehr_log_use_case import EHRLogUseCase
from app.application.ports.out.ehr_repository import EHRRepositoryPort
from app.domain.model.ehr_record import EHRRecord


class EHRLogService(EHRLogUseCase):
    """Servicio de aplicación de MS-EHRLogger.
    Recibe eventos de RabbitMQ y los persiste en MongoDB (HCD)."""

    def __init__(self, ehr_repository: EHRRepositoryPort):
        self.ehr_repository = ehr_repository

    def log_appointment(self, event: dict) -> dict:
        record = EHRRecord.from_event(event)
        saved  = self.ehr_repository.save(record)
        return {
            "mongo_id":       saved.mongo_id,
            "appointment_id": saved.appointment_id,
            "patient_id":     saved.patient_id,
            "specialty":      saved.specialty,
            "confirmed_at":   str(saved.confirmed_at),
        }

    def get_history_by_patient(self, patient_id: str) -> list:
        records = self.ehr_repository.find_by_patient(patient_id)
        return [r.to_document() for r in records]
