from flask import Blueprint, request, jsonify
from app.domain.model.appointment import ProcedureNotCoveredException, SlotNotAvailableException

appointment_bp = Blueprint("appointments", __name__)
slot_bp        = Blueprint("slots", __name__)


def create_appointment_routes(appointment_use_case):

    @appointment_bp.route("/health")
    def health():
        return {"service": "MS-AgendaHub", "status": "running"}

    @appointment_bp.route("/appointments", methods=["POST"])
    def schedule():
        data     = request.json
        required = ["patient_id", "patient_name", "doctor_id", "slot_id", "procedure_code"]
        missing  = [f for f in required if not data.get(f)]
        if missing:
            return jsonify({"error": f"Campos obligatorios: {missing}"}), 400

        try:
            result = appointment_use_case.schedule_appointment(
                patient_id=str(data["patient_id"]),
                patient_name=data["patient_name"],
                doctor_id=int(data["doctor_id"]),
                slot_id=int(data["slot_id"]),
                procedure_code=data["procedure_code"],
            )
        except ProcedureNotCoveredException as e:
            return jsonify({
                "error":          "Procedimiento no cubierto por la aseguradora",
                "rejection_code": e.rejection_code,
            }), 422
        except SlotNotAvailableException as e:
            return jsonify({"error": str(e)}), 409
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        return jsonify({"message": "Cita confirmada exitosamente", "data": result}), 201

    @appointment_bp.route("/appointments/<int:appointment_id>", methods=["GET"])
    def get_appointment(appointment_id):
        try:
            result = appointment_use_case.get_appointment(appointment_id)
        except ValueError as e:
            return jsonify({"error": str(e)}), 404
        return jsonify(result)

    @appointment_bp.route("/appointments/patient/<patient_id>", methods=["GET"])
    def list_by_patient(patient_id):
        return jsonify(appointment_use_case.list_appointments_by_patient(patient_id))

    @appointment_bp.route("/appointments/<int:appointment_id>", methods=["DELETE"])
    def cancel(appointment_id):
        try:
            result = appointment_use_case.cancel_appointment(appointment_id)
        except ValueError as e:
            return jsonify({"error": str(e)}), 404
        return jsonify({"message": "Cita cancelada", "data": result})

    return appointment_bp


def create_slot_routes(slot_use_case):

    @slot_bp.route("/slots", methods=["POST"])
    def create_slot():
        data     = request.json
        required = ["doctor_id", "doctor_name", "specialty", "slot_datetime"]
        missing  = [f for f in required if not data.get(f)]
        if missing:
            return jsonify({"error": f"Campos obligatorios: {missing}"}), 400
        try:
            result = slot_use_case.create_slot(
                doctor_id=int(data["doctor_id"]),
                doctor_name=data["doctor_name"],
                specialty=data["specialty"],
                slot_datetime=data["slot_datetime"],
            )
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        return jsonify({"message": "Slot creado", "data": result}), 201

    @slot_bp.route("/slots", methods=["GET"])
    def list_slots():
        specialty = request.args.get("specialty")
        return jsonify(slot_use_case.list_available_slots(specialty))

    return slot_bp
