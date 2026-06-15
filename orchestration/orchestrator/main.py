import logging
import os
import httpx
from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [orchestrator] %(message)s")
log = logging.getLogger(__name__)

app = FastAPI(title="orchestrator")

INVENTORY = os.environ.get("INVENTORY_URL", "http://inventory:8000")
PAYMENT = os.environ.get("PAYMENT_URL", "http://payment:8000")
SHIPPING = os.environ.get("SHIPPING_URL", "http://shipping:8000")
HTTP_TIMEOUT = float(os.environ.get("HTTP_TIMEOUT", "5.0"))


class OrderIn(BaseModel):
    order_id: str
    quantity: int = 1
    amount: int = 100


@app.post("/orders")
def create_order(order: OrderIn):
    oid = order.order_id
    log.info("=== Старт саги для заказа %s ===", oid)
    completed = []

    with httpx.Client(timeout=HTTP_TIMEOUT) as client:
        try:
            client.post(f"{INVENTORY}/reserve",
                        json={"order_id": oid, "quantity": order.quantity}).raise_for_status()
            completed.append("inventory")
        except httpx.HTTPError as e:
            log.error("Шаг 'склад' не прошёл: %s", e)
            return {"order_id": oid, "status": "FAILED", "failed_at": "inventory"}

        try:
            client.post(f"{PAYMENT}/charge",
                        json={"order_id": oid, "amount": order.amount}).raise_for_status()
            completed.append("payment")
        except httpx.HTTPError as e:
            log.error("Шаг 'оплата' не прошёл: %s -> запускаю компенсации", e)
            _compensate(client, oid, completed)
            return {"order_id": oid, "status": "FAILED", "failed_at": "payment"}

        try:
            client.post(f"{SHIPPING}/schedule", json={"order_id": oid}).raise_for_status()
            completed.append("shipping")
        except httpx.HTTPError as e:
            log.error("Шаг 'доставка' не прошёл: %s -> запускаю компенсации", e)
            _compensate(client, oid, completed)
            return {"order_id": oid, "status": "FAILED", "failed_at": "shipping"}

    log.info("=== Заказ %s успешно завершён ===", oid)
    return {"order_id": oid, "status": "COMPLETED"}


def _compensate(client: httpx.Client, oid: str, completed: list[str]):
    for step in reversed(completed):
        if step == "payment":
            client.post(f"{PAYMENT}/refund", json={"order_id": oid})
        elif step == "inventory":
            client.post(f"{INVENTORY}/release", json={"order_id": oid})


@app.get("/health")
def health():
    return {"ok": True}
