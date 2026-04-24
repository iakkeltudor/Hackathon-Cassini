from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Default placeholder for local development. Will be overwritten by env vars.
DATABASE_URL = "postgresql://user:password@localhost/cassini_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
