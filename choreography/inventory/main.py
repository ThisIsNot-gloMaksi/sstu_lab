import logging
from common import broker
import db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [inventory] %(message)s")
log = logging.getLogger("inventory")


def handler(routing_key, payload, ch):
    oid = payload["order_id"]

    if routing_key == "order.created":
        qty = payload.get("quantity", 1)
        if not db.reserve(oid, qty):
            log.warning("нет товара для %s -> inventory.failed", oid)
            broker.publish(ch, "inventory.failed", {"order_id": oid, "reason": "out_of_stock"})
            broker.publish(ch, "order.failed", {"order_id": oid, "failed_at": "inventory"})
            return
        log.info("зарезервировано %s ед. для %s (остаток %s)", qty, oid, db.available())
        broker.publish(ch, "inventory.reserved", payload)

    elif routing_key == "payment.failed":
        qty = db.release(oid)
        log.info("КОМПЕНСАЦИЯ: вернул %s ед. для %s (остаток %s)", qty, oid, db.available())


if __name__ == "__main__":
    db.init()
    broker.consume("inventory", ["order.created", "payment.failed"], handler)
