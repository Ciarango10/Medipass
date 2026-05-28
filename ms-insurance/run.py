from flask import Flask

from app.application.use_cases.insurance_service import InsuranceService
from app.infrastructure.adapters.input.insurance_controller import create_insurance_routes
from app.infrastructure.adapters.output.persistence.policy_repository_sqlalchemy import PolicyRepositorySQLAlchemy
from app.infrastructure.adapters.output.persistence.policy_entity import Base
from app.infrastructure.adapters.output.persistence.database import engine


def create_app():
    app = Flask(__name__)

    Base.metadata.create_all(engine)

    policy_repo    = PolicyRepositorySQLAlchemy()
    insurance_service = InsuranceService(policy_repo)

    app.register_blueprint(create_insurance_routes(insurance_service))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081, debug=False)
