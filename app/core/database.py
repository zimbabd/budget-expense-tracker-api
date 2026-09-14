from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Базовый класс для всех моделей SQLAlchemy (2.0-style)."""
    pass


def get_db():
    """Dependency для получения сессии БД в роутерах."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
