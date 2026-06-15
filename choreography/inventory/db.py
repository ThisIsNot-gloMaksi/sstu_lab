import os

from sqlalchemy import String, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

from common.db import connect

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./inventory.db")
INITIAL_STOCK = int(os.environ.get("INITIAL_STOCK", "5"))

_engine = None


class Base(DeclarativeBase):
    pass


class Stock(Base):
    __tablename__ = "stock"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    available: Mapped[int] = mapped_column(Integer)


class Reservation(Base):
    __tablename__ = "reservations"
    order_id: Mapped[str] = mapped_column(String, primary_key=True)
    quantity: Mapped[int] = mapped_column(Integer)


def init():
    global _engine
    _engine = connect(DATABASE_URL)
    Base.metadata.create_all(_engine)
    with Session(_engine) as s:
        if s.get(Stock, "default") is None:
            s.add(Stock(id="default", available=INITIAL_STOCK))
            s.commit()


def available() -> int:
    with Session(_engine) as s:
        return s.get(Stock, "default").available


def reserve(order_id: str, qty: int) -> bool:
    with Session(_engine) as s:
        stock = s.get(Stock, "default")
        if stock.available < qty:
            return False
        stock.available -= qty
        s.merge(Reservation(order_id=order_id, quantity=qty))
        s.commit()
        return True


def release(order_id: str) -> int:
    with Session(_engine) as s:
        r = s.get(Reservation, order_id)
        qty = r.quantity if r else 0
        if r:
            s.delete(r)
            s.get(Stock, "default").available += qty
            s.commit()
        return qty
