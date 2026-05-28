from sqlalchemy.exc import OperationalError

from app.application.ports.out.doctor_slot_repository import DoctorSlotRepositoryPort
from app.infrastructure.adapters.mappers.doctor_slot_mapper import DoctorSlotMapper
from app.infrastructure.adapters.output.persistence.database import SessionLocal
from app.infrastructure.adapters.output.persistence.doctor_slot_entity import DoctorSlotModel


class DoctorSlotRepositorySQLAlchemy(DoctorSlotRepositoryPort):

    def save(self, slot):
        session = SessionLocal()
        try:
            model = session.get(DoctorSlotModel, slot.id) if slot.id else None
            if not model:
                model = DoctorSlotMapper.to_model(slot)
                session.add(model)
                session.flush()
                slot.id = model.id
            else:
                DoctorSlotMapper.update_model(model, slot)
            session.commit()
        finally:
            session.close()
        return slot

    def get_by_id(self, slot_id):
        session = SessionLocal()
        try:
            model = session.get(DoctorSlotModel, slot_id)
            return DoctorSlotMapper.to_domain(model) if model else None
        finally:
            session.close()

    def find_available_slot_for_update(self, slot_id):
        """SELECT FOR UPDATE NOWAIT — previene double-booking concurrente.
        Retorna None si el slot ya está tomado o bloqueado por otra transacción."""
        session = SessionLocal()
        try:
            model = (
                session.query(DoctorSlotModel)
                .filter(DoctorSlotModel.id == slot_id,
                        DoctorSlotModel.status == "AVAILABLE")
                .with_for_update(nowait=True)
                .first()
            )
            if not model:
                return None
            domain = DoctorSlotMapper.to_domain(model)
            session.commit()
            return domain
        except OperationalError:
            # Otro proceso tiene el lock → slot no disponible
            session.rollback()
            return None
        finally:
            session.close()

    def list_available(self, specialty=None):
        session = SessionLocal()
        try:
            q = session.query(DoctorSlotModel).filter_by(status="AVAILABLE")
            if specialty:
                q = q.filter_by(specialty=specialty)
            return [DoctorSlotMapper.to_domain(m) for m in q.all()]
        finally:
            session.close()
