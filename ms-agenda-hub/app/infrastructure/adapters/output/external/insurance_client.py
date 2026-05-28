import os
import requests

from app.application.ports.out.insurance_validation_port import InsuranceValidationPort
from app.domain.model.insurance_coverage import InsuranceCoverage
from app.domain.model.value_objects import CoverageStatus


class InsuranceClient(InsuranceValidationPort):
    """Adaptador de salida: llama síncronamente a MS-Insurance (REST).
    Circuit breaker implícito vía timeout de 5 s."""

    def __init__(self):
        self._base_url = os.getenv("INSURANCE_SERVICE_URL", "http://ms-insurance:8081")

    def validate_coverage(self, patient_id: str, procedure_code: str) -> InsuranceCoverage:
        try:
            resp = requests.get(
                f"{self._base_url}/insurance/validate",
                params={"patient_id": patient_id, "procedure_code": procedure_code},
                timeout=5,
            )
            resp.raise_for_status()
            data = resp.json()
            return InsuranceCoverage(
                patient_id=patient_id,
                procedure_code=procedure_code,
                status=CoverageStatus(data["status"]),
                rejection_code=data.get("rejection_code"),
            )
        except requests.Timeout:
            # Aseguradora no responde → estado seguro: no confirmar
            return InsuranceCoverage(
                patient_id=patient_id,
                procedure_code=procedure_code,
                status=CoverageStatus.UNAVAILABLE,
                rejection_code="INSURANCE_TIMEOUT",
            )
        except Exception as e:
            return InsuranceCoverage(
                patient_id=patient_id,
                procedure_code=procedure_code,
                status=CoverageStatus.UNAVAILABLE,
                rejection_code=f"INSURANCE_ERROR: {str(e)}",
            )
