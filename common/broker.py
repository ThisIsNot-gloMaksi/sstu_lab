import json
import os
import time
import logging
import pika

EXCHANGE = os.environ.get("SAGA_EXCHANGE", "saga")
RABBIT_URL = os.environ.get("RABBIT_URL", "amqp://guest:guest@rabbitmq:5672/")
CONNECT_RETRIES = int(os.environ.get("RABBIT_CONNECT_RETRIES", "30"))
CONNECT_DELAY = float(os.environ.get("RABBIT_CONNECT_DELAY", "2.0"))


def connect(retries: int = CONNECT_RETRIES, delay: float = CONNECT_DELAY) -> pika.BlockingConnection:
    last_err = None
    for _ in range(retries):
        try:
            return pika.BlockingConnection(pika.URLParameters(RABBIT_URL))
        except pika.exceptions.AMQPConnectionError as e:
            last_err = e
            time.sleep(delay)
    raise RuntimeError(f"Не удалось подключиться к RabbitMQ: {last_err}")


def declare_exchange(channel):
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)


def publish(channel, routing_key: str, payload: dict):
    channel.basic_publish(
        exchange=EXCHANGE,
        routing_key=routing_key,
        body=json.dumps(payload).encode(),
        properties=pika.BasicProperties(delivery_mode=2),
    )


def consume(service_name: str, binding_keys: list, handler):
    log = logging.getLogger(service_name)
    conn = connect()
    channel = conn.channel()
    declare_exchange(channel)

    queue = f"{service_name}.queue"
    channel.queue_declare(queue=queue, durable=True)
    for key in binding_keys:
        channel.queue_bind(exchange=EXCHANGE, queue=queue, routing_key=key)

    channel.basic_qos(prefetch_count=1)

    def _on_message(ch, method, properties, body):
        payload = json.loads(body)
        log.info("получено событие '%s': %s", method.routing_key, payload)
        try:
            handler(method.routing_key, payload, ch)
        finally:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=queue, on_message_callback=_on_message)
    log.info("слушаю %s ...", binding_keys)
    channel.start_consuming()
