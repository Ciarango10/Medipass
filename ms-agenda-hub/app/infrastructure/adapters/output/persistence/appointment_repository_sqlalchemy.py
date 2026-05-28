from app.application.ports.out.appointment_repository import AppointmentRepositoryPort
from app.infrastructure.adapters.mappers.appointment_mapper import AppointmentMapper
from app.infrastructure.adapters.output.persistence.database import SessionLocal
from app.infrastructure.adapters.output.persistence.appointment_entity import AppointmentModel


class AppointmentRepositorySQLAlchemy(AppointmentRepositoryPort):

    def save(self, appointment):
        session = SessionLocal()
        try:
            model = session.get(AppointmentModel, appointment.id) if appointment.id else None
            if not model:
                model = AppointmentMapper.to_model(appointment)
                session.add(model)
                session.flush()
                appointment.id = model.id
            else:
                AppointmentMapper.update_model(model, appointment)
            session.commit()
        finally:
            session.close()
        return appointment

    def get_by_id(self, appointment_id):
        session = SessionLocal()
        try:
            model = session.get(AppointmentModel, appointment_id)
            return AppointmentMapper.to_domain(model) if model else None
        finally:
            session.close()

    def list_by_patient(self, patient_id):
        session = SessionLocal()
        try:
            models = session.query(AppointmentModel).filter_by(patient_id=patient_id).all()
            return [AppointmentMapper.to_domain(m) for m in models]
        finally:
            session.close()

    def delete(self, appointment_id):
        session = SessionLocal()
        try:
            model = session.get(AppointmentModel, appointment_id)
            if model:
                session.delete(model)
                session.commit()
        finally:
            session.close()
