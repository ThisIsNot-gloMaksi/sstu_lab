import os
import time
import uuid

import requests

ORDER_URL = os.environ.get("ORDER_URL", "http://localhost:8000").rstrip("/")
ANTIFRAUD_URL = os.environ.get("ANTIFRAUD_URL", "http://localhost:8010").rstrip("/")
TIMEOUT = float(os.environ.get("POLL_TIMEOUT", "20"))
FRAUD_LIMIT = int(os.environ.get("FRAUD_LIMIT", "3000"))
PAYMENT_LIMIT = int(os.environ.get("PAYMENT_LIMIT", "1000"))
INITIAL_STOCK = int(os.environ.get("INITIAL_STOCK", "5"))


def _oid(prefix):
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def place(order_id, quantity=1, amount=100):
    r = requests.post(f"{ORDER_URL}/orders",
                      json={"order_id": order_id, "quantity": quantity, "amount": amount},
                      timeout=5)
    r.raise_for_status()
    return r.json()


def wait_final(order_id, immediate):
    if immediate.get("status") in ("COMPLETED", "FAILED"):
        return immediate
    deadline = time.time() + TIMEOUT
    while time.time() < deadline:
        r = requests.get(f"{ORDER_URL}/orders/{order_id}", timeout=5)
        if r.ok and r.json().get("status") in ("COMPLETED", "FAILED"):
            return r.json()
        time.sleep(0.4)
    raise AssertionError(f"заказ {order_id} не дошёл до финального статуса за {TIMEOUT}s")


def wait_decision(order_id, expected):
    deadline = time.time() + TIMEOUT
    last = None
    while time.time() < deadline:
        r = requests.get(f"{ANTIFRAUD_URL}/antifraud/{order_id}", timeout=5)
        if r.ok:
            last = r.json().get("decision")
            if last == expected:
                return last
        time.sleep(0.4)
    raise AssertionError(f"antifraud по {order_id}: ждал '{expected}', получил '{last}'")

def test_services_reachable():
    assert requests.get(f"{ORDER_URL}/health", timeout=5).ok, "сервис order/orchestrator недоступен"
    assert requests.get(f"{ANTIFRAUD_URL}/health", timeout=5).ok, "сервис antifraud недоступен"


def test_normal_order_completes_and_passes_antifraud():
    oid = _oid("ok")
    res = wait_final(oid, place(oid, quantity=1, amount=100))
    assert res["status"] == "COMPLETED", f"ожидал COMPLETED, получил {res}"
    assert wait_decision(oid, "passed") == "passed"


def test_fraud_order_is_rejected():
    oid = _oid("fraud")
    res = wait_final(oid, place(oid, quantity=1, amount=FRAUD_LIMIT + 2000))
    assert res["status"] == "FAILED", f"ожидал FAILED, получил {res}"
    assert wait_decision(oid, "rejected") == "rejected"
    if "failed_at" in res:
        assert res["failed_at"] == "antifraud", f"сбой не на антифроде: {res}"


def test_fraud_rejection_compensates_inventory():
    fid = _oid("comp-fraud")
    res = wait_final(fid, place(fid, quantity=INITIAL_STOCK, amount=FRAUD_LIMIT + 2000))
    assert res["status"] == "FAILED", f"фрод-заказ должен упасть, получил {res}"

    deadline = time.time() + TIMEOUT
    last = None
    while time.time() < deadline:
        rid = _oid("comp-ok")
        last = wait_final(rid, place(rid, quantity=INITIAL_STOCK, amount=100))
        if last["status"] == "COMPLETED":
            break
        time.sleep(0.5)
    assert last and last["status"] == "COMPLETED", \
        "склад не освободился после отклонения антифродом — компенсация не сработала"
