from app.domain.model.doctor_slot import DoctorSlot
from app.infrastructure.adapters.output.persistence.doctor_slot_entity import DoctorSlotModel


class DoctorSlotMapper:

    @staticmethod
    def to_domain(model: DoctorSlotModel) -> DoctorSlot:
        return DoctorSlot(
            id=model.id,
            doctor_id=model.doctor_id,
            doctor_name=model.doctor_name,
            specialty=model.specialty,
            slot_datetime=model.slot_datetime,
            status=model.status,
        )

    @staticmethod
    def to_model(slot: DoctorSlot) -> DoctorSlotModel:
        return DoctorSlotModel(
            id=slot.id,
            doctor_id=slot.doctor_id,
            doctor_name=slot.doctor_name,
            specialty=slot.specialty.value if hasattr(slot.specialty, "value") else slot.specialty,
            slot_datetime=slot.slot_datetime,
            status=slot.status.value if hasattr(slot.status, "value") else slot.status,
        )

    @staticmethod
    def update_model(model: DoctorSlotModel, slot: DoctorSlot) -> None:
        model.status = slot.status.value if hasattr(slot.status, "value") else slot.status
