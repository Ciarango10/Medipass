"""MS-EHRLogger — Worker asíncrono.
Patrón idéntico a worker.py de ClubFit:
proceso separado que escucha el broker y persiste en MongoDB."""

import logging
import signal
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ehr-worker")

from app.application.use_cases.ehr_log_service import EHRLogService
from app.infrastructure.adapters.output.persistence.ehr_repository_mongodb import EHRRepositoryMongoDB
from app.infrastructure.adapters.input.rabbitmq_subscriber import RabbitMQSubscriber


def main():
    ehr_repo       = EHRRepositoryMongoDB()
    ehr_service    = EHRLogService(ehr_repo)
    subscriber     = RabbitMQSubscriber(ehr_service)

    def shutdown(sig, frame):
        logger.info("Apagando EHR worker...")
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT,  shutdown)

    logger.info("EHR Worker iniciado. Esperando eventos de agenda...")
    subscriber.start_listening()


if __name__ == "__main__":
    main()
