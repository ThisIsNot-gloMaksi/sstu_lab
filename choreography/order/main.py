import logging
import threading

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from common import broker
import db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [order] %(message)s")
log = logging.getLogger("order")

app = FastAPI(title="order")

_pub_conn = None
_pub_channel = None


def _ensure_publisher():
    global _pub_conn, _pub_channel
    if _pub_channel is None or _pub_conn.is_closed:
        _pub_conn = broker.connect()
        _pub_channel = _pub_conn.channel()
        broker.declare_exchange(_pub_channel)
    return _pub_channel


class OrderIn(BaseModel):
    order_id: str
    quantity: int = 1
    amount: int = 100


@app.post("/orders")
def create_order(order: OrderIn):
    db.create(order.order_id, order.quantity, order.amount)
    ch = _ensure_publisher()
    broker.publish(ch, "order.created", order.model_dump())
    log.info("опубликовано order.created для %s", order.order_id)
    return {"order_id": order.order_id, "status": "PENDING"}


@app.get("/orders/{order_id}")
def get_order(order_id: str):
    return db.get(order_id)


@app.get("/health")
def health():
    return {"ok": True}


def _final_handler(routing_key, payload, ch):
    oid = payload.get("order_id")
    status = "COMPLETED" if routing_key == "order.completed" else "FAILED"
    if db.set_status(oid, status):
        log.info("заказ %s -> %s", oid, status)


def _start_consumer():
    broker.consume("order", ["order.completed", "order.failed"], _final_handler)


if __name__ == "__main__":
    db.init()
    threading.Thread(target=_start_consumer, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=8000)
