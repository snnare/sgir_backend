from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config_core import settings

engine = create_engine(settings.ORACLE10_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_oracle10_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
