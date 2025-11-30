import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import settings


# Create a synchronous engine. For local development default is sqlite.
DATABASE_URL = os.getenv("DATABASE_URL") or settings.DATABASE_URL

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_session():
    """Yield a SQLAlchemy session (use with context manager or try/finally).

    Example:
        with get_session() as session:
            ...
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
