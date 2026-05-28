from app.application.ports.input.insurance_use_case import InsuranceUseCase
from app.application.ports.out.policy_repository import PolicyRepositoryPort
from app.domain.model.coverage import CoverageResult
from app.domain.model.value_objects import CoverageStatus


class InsuranceService(InsuranceUseCase):
    """Proxy hacia el catálogo de pólizas (simula Oracle 19c via SQLAlchemy).
    Aplica Anti-Corruption Layer: traduce pólizas de BD a CoverageResult limpio."""

    def __init__(self, policy_repository: PolicyRepositoryPort):
        self.policy_repository = policy_repository

    def validate_coverage(self, patient_id: str, procedure_code: str) -> dict:
        policy = self.policy_repository.find_policy(patient_id, procedure_code)

        if policy is None:
            result = CoverageResult(
                patient_id=patient_id,
                procedure_code=procedure_code,
                status=CoverageStatus.NOT_COVERED,
                rejection_code="POLICY_NOT_FOUND",
            )
        elif policy.covered:
            result = CoverageResult(
                patient_id=patient_id,
                procedure_code=procedure_code,
                status=CoverageStatus.COVERED,
            )
        else:
            result = CoverageResult(
                patient_id=patient_id,
                procedure_code=procedure_code,
                status=CoverageStatus.NOT_COVERED,
                rejection_code=policy.rejection_code or "PROCEDURE_EXCLUDED",
            )

        return result.to_dict()

    def seed_policies(self) -> dict:
        """Carga datos de prueba (simula catálogo Oracle)."""
        seeds = [
            ("P001", "CHT-001", True,  None),
            ("P001", "CARD-002", True,  None),
            ("P002", "CHT-001", False, "PROCEDURE_EXCLUDED"),
            ("P002", "CARD-002", True,  None),
            ("P003", "CHT-001", True,  None),
        ]
        for patient_id, proc, covered, rejection in seeds:
            self.policy_repository.save_policy(patient_id, proc, covered, rejection)
        return {"message": f"{len(seeds)} pólizas cargadas"}
