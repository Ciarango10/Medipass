from flask import Blueprint, request, jsonify

insurance_bp = Blueprint("insurance", __name__)


def create_insurance_routes(use_case):

    @insurance_bp.route("/")
    def health():
        return {"service": "MS-Insurance", "status": "running"}

    @insurance_bp.route("/insurance/validate", methods=["GET"])
    def validate():
        patient_id     = request.args.get("patient_id")
        procedure_code = request.args.get("procedure_code")
        if not patient_id or not procedure_code:
            return jsonify({"error": "patient_id y procedure_code son requeridos"}), 400

        result = use_case.validate_coverage(patient_id, procedure_code)
        return jsonify(result)

    @insurance_bp.route("/insurance/seed", methods=["POST"])
    def seed():
        result = use_case.seed_policies()
        return jsonify(result), 201

    return insurance_bp
