import logging
from common import broker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [shipping] %(message)s")
log = logging.getLogger("shipping")


def handler(routing_key, payload, ch):
    oid = payload["order_id"]
    log.info("доставка запланирована для %s -> order.completed", oid)
    broker.publish(ch, "order.completed", {"order_id": oid})


if __name__ == "__main__":
    broker.consume("shipping", ["payment.completed"], handler)
