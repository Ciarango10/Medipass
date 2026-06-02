from datetime import datetime
from typing import List, Optional
from dataclasses import asdict

from app.application.ports.input.appointment_use_case import AppointmentUseCase, DoctorSlotUseCase
from app.application.ports.out.appointment_repository import AppointmentRepositoryPort
from app.application.ports.out.doctor_slot_repository import DoctorSlotRepositoryPort
from app.application.ports.out.insurance_validation_port import InsuranceValidationPort
from app.application.ports.out.event_publisher import EventPublisherPort
from app.domain.model.appointment import Appointment, ProcedureNotCoveredException, SlotNotAvailableException
from app.domain.model.doctor_slot import DoctorSlot
from app.domain.model.value_objects import CoverageStatus, SlotStatus, AppointmentStatus


class AppointmentService(AppointmentUseCase):

    def __init__(self,
                 appointment_repository: AppointmentRepositoryPort,
                 slot_repository: DoctorSlotRepositoryPort,
                 insurance_port: InsuranceValidationPort,
                 event_publisher: EventPublisherPort):
        self.appointment_repo = appointment_repository
        self.slot_repo        = slot_repository
        self.insurance_port   = insurance_port
        self.event_publisher  = event_publisher

    def schedule_appointment(self, patient_id: str, patient_name: str,
                             doctor_id: int, slot_id: int, procedure_code: str) -> dict:
        # 1. Validar cobertura con MS-Insurance
        coverage = self.insurance_port.validate_coverage(patient_id, procedure_code)
        if coverage.status == CoverageStatus.NOT_COVERED:
            raise ProcedureNotCoveredException(coverage.rejection_code or "NOT_COVERED")
        
        # 2. Bloquear slot con SELECT FOR UPDATE NOWAIT
        slot = self.slot_repo.find_available_slot_for_update(slot_id)
        if not slot or slot.doctor_id != doctor_id:
            raise SlotNotAvailableException("El slot no está disponible o no pertenece al doctor")

        # 3. Crear cita
        appointment = Appointment(
            id=None,
            patient_id=patient_id,
            patient_name=patient_name,
            doctor_id=doctor_id,
            slot_id=slot_id,
            procedure_code=procedure_code,
            coverage_status=coverage.status.value,
            rejection_code=coverage.rejection_code,
            status=AppointmentStatus.CONFIRMED,
            created_at=datetime.now()
        )
        saved_appt = self.appointment_repo.save(appointment)

        # 4. Actualizar status del slot
        slot.status = SlotStatus.CONFIRMED
        self.slot_repo.save(slot)

        # 5. Publicar evento para EHR Logger (asíncrono)
        event = {
            "event":           "APPOINTMENT_CONFIRMED",
            "appointment_id":  saved_appt.id,
            "patient_id":      saved_appt.patient_id,
            "patient_name":    saved_appt.patient_name,
            "doctor_id":       saved_appt.doctor_id,
            "doctor_name":     slot.doctor_name,
            "specialty":       slot.specialty,
            "procedure_code":  saved_appt.procedure_code,
            "coverage_status": saved_appt.coverage_status,
            "slot_datetime":   str(slot.slot_datetime),
        }
        self.event_publisher.publish("agenda.confirmed", event)

        return asdict(saved_appt)

    def get_appointment(self, appointment_id: int) -> dict:
        appt = self.appointment_repo.get_by_id(appointment_id)
        if not appt:
            raise ValueError("Cita no encontrada")
        return asdict(appt)

    def list_appointments_by_patient(self, patient_id: str) -> List[dict]:
        appts = self.appointment_repo.list_by_patient(patient_id)
        return [asdict(a) for a in appts]

    def cancel_appointment(self, appointment_id: int) -> dict:
        appt = self.appointment_repo.get_by_id(appointment_id)
        if not appt:
            raise ValueError("Cita no encontrada")
        
        appt.status = AppointmentStatus.CANCELLED
        self.appointment_repo.save(appt)

        slot = self.slot_repo.get_by_id(appt.slot_id)
        if slot:
            slot.status = SlotStatus.AVAILABLE
            self.slot_repo.save(slot)

        return asdict(appt)


class DoctorSlotService(DoctorSlotUseCase):

    def __init__(self, slot_repository: DoctorSlotRepositoryPort):
        self.slot_repo = slot_repository

    def create_slot(self, doctor_id: int, doctor_name: str,
                    specialty: str, slot_datetime: str) -> dict:
        dt = datetime.fromisoformat(slot_datetime)
        slot = DoctorSlot(
            id=None,
            doctor_id=doctor_id,
            doctor_name=doctor_name,
            specialty=specialty,
            slot_datetime=dt,
            status=SlotStatus.AVAILABLE
        )
        saved_slot = self.slot_repo.save(slot)
        return asdict(saved_slot)

    def list_available_slots(self, specialty: Optional[str] = None) -> List[dict]:
        slots = self.slot_repo.list_available(specialty)
        return [asdict(s) for s in slots]
