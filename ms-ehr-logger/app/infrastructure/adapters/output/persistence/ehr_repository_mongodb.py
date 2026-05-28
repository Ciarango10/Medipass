import os
from pymongo import MongoClient

from app.application.ports.out.ehr_repository import EHRRepositoryPort
from app.domain.model.ehr_record import EHRRecord


class EHRRepositoryMongoDB(EHRRepositoryPort):
    """Adaptador de salida: persiste registros clínicos en MongoDB.
    Mismo patrón que MemberRepositorySQLAlchemy en ClubFit,
    cambiando SQLAlchemy por PyMongo."""

    def __init__(self):
        mongo_uri   = os.getenv("MONGO_URI", "mongodb://mongodb:27017/")
        db_name     = os.getenv("MONGO_DB",  "hcd")
        client      = MongoClient(mongo_uri)
        self._col   = client[db_name]["ehr_records"]

    def save(self, record: EHRRecord) -> EHRRecord:
        doc         = record.to_document()
        result      = self._col.insert_one(doc)
        record.mongo_id = str(result.inserted_id)
        return record

    def find_by_patient(self, patient_id: str) -> list:
        docs = self._col.find({"patient_id": patient_id}, {"_id": 0})
        return [
            EHRRecord(
                appointment_id  = d["appointment_id"],
                patient_id      = d["patient_id"],
                patient_name    = d["patient_name"],
                doctor_id       = d["doctor_id"],
                doctor_name     = d.get("doctor_name", ""),
                specialty       = d.get("specialty", ""),
                procedure_code  = d["procedure_code"],
                coverage_status = d.get("coverage_status", ""),
                slot_datetime   = d.get("slot_datetime", ""),
                confirmed_at    = d.get("confirmed_at", ""),
            )
            for d in docs
        ]
