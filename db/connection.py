from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager

DATABASE_URL = (
    "mssql+pyodbc://(localdb)\\MSSQLLocalDB/Integration_Gateway_DB?"
    "driver=ODBC+Driver+17+for+SQL+Server&"
    "trusted_connection=yes&Encrypt=no"
)

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
Base = declarative_base()

@contextmanager
def transaction_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()