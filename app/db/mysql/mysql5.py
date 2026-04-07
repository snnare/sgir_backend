from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from app.core.config import settings

engine: Engine = create_engine(url=settings.MYSQL5_DATABASE_URL)
SessionLocal: sessionmaker[Session]
