from app.application.ports.out.policy_repository import PolicyRepositoryPort
from app.infrastructure.adapters.output.persistence.database import SessionLocal
from app.infrastructure.adapters.output.persistence.policy_entity import PolicyModel


class PolicyRepositorySQLAlchemy(PolicyRepositoryPort):

    def find_policy(self, patient_id: str, procedure_code: str):
        session = SessionLocal()
        try:
            return (session.query(PolicyModel)
                    .filter_by(patient_id=patient_id, procedure_code=procedure_code)
                    .first())
        finally:
            session.close()

    def save_policy(self, patient_id, procedure_code, covered, rejection_code=None):
        session = SessionLocal()
        try:
            existing = (session.query(PolicyModel)
                        .filter_by(patient_id=patient_id, procedure_code=procedure_code)
                        .first())
            if existing:
                existing.covered        = covered
                existing.rejection_code = rejection_code
            else:
                session.add(PolicyModel(
                    patient_id=patient_id,
                    procedure_code=procedure_code,
                    covered=covered,
                    rejection_code=rejection_code,
                ))
            session.commit()
        finally:
            session.close()
