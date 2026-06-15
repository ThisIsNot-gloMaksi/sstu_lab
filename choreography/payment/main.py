import logging
import os
from common import broker
import db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [payment] %(message)s")
log = logging.getLogger("payment")

LIMIT = int(os.environ.get("PAYMENT_LIMIT", "1000"))


def handler(routing_key, payload, ch):
    oid = payload["order_id"]
    amount = payload.get("amount", 100)

    if amount > LIMIT:
        log.warning("платёж отклонён для %s (сумма %s) -> payment.failed", oid, amount)
        broker.publish(ch, "payment.failed", {"order_id": oid, "reason": "declined"})
        broker.publish(ch, "order.failed", {"order_id": oid, "failed_at": "payment"})
        return

    db.charge(oid, amount)
    log.info("списано %s для %s -> payment.completed", amount, oid)
    broker.publish(ch, "payment.completed", payload)


if __name__ == "__main__":
    db.init()
    broker.consume("payment", ["inventory.reserved"], handler)
