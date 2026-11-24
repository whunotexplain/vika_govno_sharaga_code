from DB_Units.config import connection
from DB_Units.models import Base

def init_database():
    try:
        connection.init()
        Base.metadata.create_all(connection.engine)
    except Exception as error:
        raise RuntimeError(
            "Не удалось подключиться к PostgreSQL. Проверь .env, сервер и базу shop_db. "
            f"Подробности: {error}"
        ) from error

def get_session():
    return connection.Session()
