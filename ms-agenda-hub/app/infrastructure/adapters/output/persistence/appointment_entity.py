from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class AppointmentModel(Base):

    __tablename__ = "appointments"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    patient_id       = Column(String,  nullable=False)
    patient_name     = Column(String,  nullable=False)
    doctor_id        = Column(Integer, nullable=False)
    slot_id          = Column(Integer, nullable=False)
    procedure_code   = Column(String,  nullable=False)
    coverage_status  = Column(String,  nullable=False)
    rejection_code   = Column(String,  nullable=True)
    status           = Column(String,  nullable=False, default="CONFIRMED")
    created_at       = Column(DateTime, nullable=False)
