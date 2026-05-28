import json
import logging
import os
import pika

logger = logging.getLogger(__name__)


class RabbitMQSubscriber:
    """Adaptador de entrada asíncrono.
    Patrón idéntico a RedisSubscriber en ClubFit,
    consumiendo de RabbitMQ en lugar de Redis Pub/Sub."""

    def __init__(self, ehr_use_case):
        self.ehr_use_case = ehr_use_case
        self._url         = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
        self._queue       = os.getenv("RABBITMQ_QUEUE", "agenda.confirmed")

    def start_listening(self):
        connection = pika.BlockingConnection(pika.URLParameters(self._url))
        channel    = connection.channel()
        channel.queue_declare(queue=self._queue, durable=True)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=self._queue, on_message_callback=self._handle)

        logger.info("EHRLogger escuchando cola '%s'...", self._queue)
        channel.start_consuming()

    def _handle(self, ch, method, properties, body):
        try:
            event = json.loads(body)
            if event.get("event") == "APPOINTMENT_CONFIRMED":
                result = self.ehr_use_case.log_appointment(event)
                logger.info("HCD actualizado: %s", result)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error("Error procesando evento: %s", e)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
