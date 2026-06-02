from flask import Flask

from app.application.use_cases.appointment_service import AppointmentService, DoctorSlotService
from app.infrastructure.adapters.input.appointment_controller import (
    create_appointment_routes, create_slot_routes,
)
from app.infrastructure.adapters.input.ui_controller import create_ui_routes
from app.infrastructure.adapters.output.persistence.appointment_repository_sqlalchemy import (
    AppointmentRepositorySQLAlchemy,
)
from app.infrastructure.adapters.output.persistence.doctor_slot_repository_sqlalchemy import (
    DoctorSlotRepositorySQLAlchemy,
)
from app.infrastructure.adapters.output.messaging.rabbitmq_publisher import RabbitMQPublisher
from app.infrastructure.adapters.output.external.insurance_client import InsuranceClient
from app.infrastructure.adapters.output.persistence.appointment_entity import Base as AppointmentBase
from app.infrastructure.adapters.output.persistence.doctor_slot_entity import Base as SlotBase
from app.infrastructure.adapters.output.persistence.database import engine


def create_app():
    app = Flask(__name__)

    # Crear tablas en PostgreSQL
    AppointmentBase.metadata.create_all(engine)
    SlotBase.metadata.create_all(engine)

    # ── Inyección de dependencias (igual que ClubFit run.py) ────────
    appointment_repo = AppointmentRepositorySQLAlchemy()
    slot_repo        = DoctorSlotRepositorySQLAlchemy()
    insurance_port   = InsuranceClient()
    publisher        = RabbitMQPublisher()

    appointment_service = AppointmentService(
        appointment_repository=appointment_repo,
        slot_repository=slot_repo,
        insurance_port=insurance_port,
        event_publisher=publisher,
    )
    slot_service = DoctorSlotService(slot_repository=slot_repo)

    app.register_blueprint(create_appointment_routes(appointment_service))
    app.register_blueprint(create_slot_routes(slot_service))
    app.register_blueprint(create_ui_routes())

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
