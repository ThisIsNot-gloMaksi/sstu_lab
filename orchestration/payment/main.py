import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [payment] %(message)s")
log = logging.getLogger(__name__)

LIMIT = int(os.environ.get("PAYMENT_LIMIT", "1000"))


@asynccontextmanager
async def lifespan(app):
    db.init()
    yield


app = FastAPI(title="payment", lifespan=lifespan)


class ChargeIn(BaseModel):
    order_id: str
    amount: int


@app.post("/charge")
def charge(req: ChargeIn):
    if req.amount > LIMIT:
        log.warning("Платёж отклонён для заказа %s (сумма %s > лимит %s)",
                    req.order_id, req.amount, LIMIT)
        raise HTTPException(status_code=402, detail="payment_declined")
    db.charge(req.order_id, req.amount)
    log.info("Списано %s для заказа %s", req.amount, req.order_id)
    return {"status": "charged", "order_id": req.order_id}


class RefundIn(BaseModel):
    order_id: str


@app.post("/refund")
def refund(req: RefundIn):
    amount = db.refund(req.order_id)
    log.info("КОМПЕНСАЦИЯ: возврат %s для заказа %s", amount, req.order_id)
    return {"status": "refunded", "order_id": req.order_id}


@app.get("/health")
def health():
    return {"ok": True}
