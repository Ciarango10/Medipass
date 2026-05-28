from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class DoctorSlotModel(Base):

    __tablename__ = "doctor_slots"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    doctor_id     = Column(Integer, nullable=False)
    doctor_name   = Column(String,  nullable=False)
    specialty     = Column(String,  nullable=False)
    slot_datetime = Column(DateTime, nullable=False)
    status        = Column(String,  nullable=False, default="AVAILABLE")
