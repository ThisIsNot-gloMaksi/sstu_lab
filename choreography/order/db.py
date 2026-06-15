import os

from sqlalchemy import String, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

from common.db import connect

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./order.db")

_engine = None


class Base(DeclarativeBase):
    pass


class Order(Base):
    __tablename__ = "orders"
    order_id: Mapped[str] = mapped_column(String, primary_key=True)
    status: Mapped[str] = mapped_column(String)
    quantity: Mapped[int] = mapped_column(Integer)
    amount: Mapped[int] = mapped_column(Integer)


def init():
    global _engine
    _engine = connect(DATABASE_URL)
    Base.metadata.create_all(_engine)


def create(order_id: str, quantity: int, amount: int):
    with Session(_engine) as s:
        s.merge(Order(order_id=order_id, status="PENDING", quantity=quantity, amount=amount))
        s.commit()


def set_status(order_id: str, status: str) -> bool:
    with Session(_engine) as s:
        o = s.get(Order, order_id)
        if o is None:
            return False
        o.status = status
        s.commit()
        return True


def get(order_id: str) -> dict:
    with Session(_engine) as s:
        o = s.get(Order, order_id)
        if o is None:
            return {"status": "UNKNOWN"}
        return {"order_id": o.order_id, "status": o.status,
                "quantity": o.quantity, "amount": o.amount}
