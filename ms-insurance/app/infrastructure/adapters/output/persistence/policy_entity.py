from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class PolicyModel(Base):
    """Simula la tabla de pólizas en Oracle 19c.
    En producción este adaptador usaría cx_Oracle como driver."""

    __tablename__ = "insurance_policies"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    patient_id     = Column(String,  nullable=False, index=True)
    procedure_code = Column(String,  nullable=False, index=True)
    covered        = Column(Boolean, nullable=False, default=True)
    rejection_code = Column(String,  nullable=True)
