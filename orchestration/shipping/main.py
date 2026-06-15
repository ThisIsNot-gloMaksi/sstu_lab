import logging
from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [shipping] %(message)s")
log = logging.getLogger(__name__)

app = FastAPI(title="shipping")


class ShipIn(BaseModel):
    order_id: str


@app.post("/schedule")
def schedule(req: ShipIn):
    log.info("Доставка запланирована для заказа %s", req.order_id)
    return {"status": "scheduled", "order_id": req.order_id}


@app.get("/health")
def health():
    return {"ok": True}
