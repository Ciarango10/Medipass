import json
import os
import pika

from app.application.ports.out.event_publisher import EventPublisherPort


class RabbitMQPublisher(EventPublisherPort):
    """Adaptador de salida: publica mensajes en RabbitMQ (AMQP 0-9-1).
    Patrón idéntico a RedisPublisher en ClubFit, cambiando el broker."""

    def __init__(self):
        self._url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

    def publish(self, queue: str, message: dict) -> None:
        connection = pika.BlockingConnection(pika.URLParameters(self._url))
        channel    = connection.channel()
        channel.queue_declare(queue=queue, durable=True)
        channel.basic_publish(
            exchange="",
            routing_key=queue,
            body=json.dumps(message, default=str),
            properties=pika.BasicProperties(delivery_mode=2),  # persistent
        )
        connection.close()
