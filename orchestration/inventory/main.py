import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [inventory] %(message)s")
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app):
    db.init()
    yield


app = FastAPI(title="inventory", lifespan=lifespan)


class ReserveIn(BaseModel):
    order_id: str
    quantity: int


@app.post("/reserve")
def reserve(req: ReserveIn):
    if not db.reserve(req.order_id, req.quantity):
        log.warning("Недостаточно товара для заказа %s (нужно %s, есть %s)",
                    req.order_id, req.quantity, db.available())
        raise HTTPException(status_code=409, detail="out_of_stock")
    log.info("Зарезервировано %s ед. для заказа %s (остаток %s)",
             req.quantity, req.order_id, db.available())
    return {"status": "reserved", "order_id": req.order_id}


class ReleaseIn(BaseModel):
    order_id: str


@app.post("/release")
def release(req: ReleaseIn):
    qty = db.release(req.order_id)
    log.info("КОМПЕНСАЦИЯ: возвращено %s ед. для заказа %s (остаток %s)",
             qty, req.order_id, db.available())
    return {"status": "released", "order_id": req.order_id}


@app.get("/health")
def health():
    return {"ok": True, "stock": db.available()}
