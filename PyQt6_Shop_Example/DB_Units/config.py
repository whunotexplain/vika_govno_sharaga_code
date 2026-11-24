import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

class Connection:
    """Настройки PostgreSQL и фабрика SQLAlchemy-сессий."""
    def __init__(self):
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "postgres")
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        database = os.getenv("DB_NAME", "shop_db")
        self.url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"
        self.engine = create_engine(self.url, pool_pre_ping=True)
        self.Session = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)

    def init(self):
        from sqlalchemy import text
        with self.engine.connect() as db:
            db.execute(text("SELECT 1"))
        return True

connection = Connection()
