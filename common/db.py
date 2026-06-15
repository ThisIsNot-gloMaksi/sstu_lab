import time

from sqlalchemy import create_engine, text


def connect(database_url: str, retries: int = 30, delay: float = 2.0):
    last = None
    for _ in range(retries):
        try:
            eng = create_engine(database_url)
            with eng.connect() as c:
                c.execute(text("SELECT 1"))
            return eng
        except Exception as e:
            last = e
            time.sleep(delay)
    raise RuntimeError(f"БД недоступна: {last}")
