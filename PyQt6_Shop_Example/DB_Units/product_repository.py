from sqlalchemy import select, func
from DB_Units.database import get_session
from DB_Units.models import Product

class ProductRepository:
    @staticmethod
    def count():
        with get_session() as session:
            return session.scalar(select(func.count(Product.id))) or 0

    @staticmethod
    def categories():
        with get_session() as session:
            return list(session.scalars(select(Product.category).distinct().order_by(Product.category)))

    @staticmethod
    def get_all(search="", category="Все", min_price=0, max_price=None, sort="Название"):
        query = select(Product).where(Product.price >= min_price)
        if search:
            query = query.where(Product.name.ilike(f"%{search}%"))
        if category != "Все":
            query = query.where(Product.category == category)
        if max_price is not None:
            query = query.where(Product.price <= max_price)
        if sort == "Цена: по возрастанию":
            query = query.order_by(Product.price.asc())
        elif sort == "Цена: по убыванию":
            query = query.order_by(Product.price.desc())
        else:
            query = query.order_by(Product.name.asc())
        with get_session() as session:
            return list(session.scalars(query))
