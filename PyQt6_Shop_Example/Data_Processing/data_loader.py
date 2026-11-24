from DB_Units.database import get_session
from DB_Units.models import Product
from Data_Processing.excel_processor import read_products

def import_products(path):
    frame = read_products(path)
    with get_session() as session:
        for row in frame.to_dict(orient="records"):
            product = session.query(Product).filter_by(name=row["name"]).first()
            fields = dict(category=row["category"], description=row["description"], price=row["price"], stock=row["stock"])
            if product:
                for key, value in fields.items():
                    setattr(product, key, value)
            else:
                session.add(Product(name=row["name"], **fields))
        session.commit()
    return len(frame)
