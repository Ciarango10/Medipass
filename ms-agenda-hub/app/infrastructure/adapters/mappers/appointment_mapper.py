from datetime import datetime
from app.domain.model.appointment import Appointment
from app.infrastructure.adapters.output.persistence.appointment_entity import AppointmentModel


class AppointmentMapper:

    @staticmethod
    def to_domain(model: AppointmentModel) -> Appointment:
        return Appointment(
            id=model.id,
            patient_id=model.patient_id,
            patient_name=model.patient_name,
            doctor_id=model.doctor_id,
            slot_id=model.slot_id,
            procedure_code=model.procedure_code,
            coverage_status=model.coverage_status,
            rejection_code=model.rejection_code,
            status=model.status,
            created_at=model.created_at,
        )

    @staticmethod
    def to_model(appt: Appointment) -> AppointmentModel:
        return AppointmentModel(
            id=appt.id,
            patient_id=appt.patient_id,
            patient_name=appt.patient_name,
            doctor_id=appt.doctor_id,
            slot_id=appt.slot_id,
            procedure_code=appt.procedure_code,
            coverage_status=appt.coverage_status,
            rejection_code=appt.rejection_code,
            status=appt.status.value if hasattr(appt.status, "value") else appt.status,
            created_at=appt.created_at or datetime.now(),
        )

    @staticmethod
    def update_model(model: AppointmentModel, appt: Appointment) -> None:
        model.status = appt.status.value if hasattr(appt.status, "value") else appt.status
