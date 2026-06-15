import os

from sqlalchemy import String, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

from common.db import connect

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./payment.db")

_engine = None


class Base(DeclarativeBase):
    pass


class Charge(Base):
    __tablename__ = "charges"
    order_id: Mapped[str] = mapped_column(String, primary_key=True)
    amount: Mapped[int] = mapped_column(Integer)


def init():
    global _engine
    _engine = connect(DATABASE_URL)
    Base.metadata.create_all(_engine)


def charge(order_id: str, amount: int):
    with Session(_engine) as s:
        s.merge(Charge(order_id=order_id, amount=amount))
        s.commit()
