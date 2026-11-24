from decimal import Decimal
from DB_Units.database import get_session
from DB_Units.models import Order, OrderItem, Product

class OrderRepository:
    @staticmethod
    def create(customer_name, cart):
        with get_session() as session:
            try:
                total = sum((Decimal(str(x["price"])) * x["quantity"] for x in cart.values()), Decimal("0.00"))
                order = Order(customer_name=customer_name, total=total)
                session.add(order)
                session.flush()
                for product_id, item in cart.items():
                    product = session.get(Product, product_id)
                    if product is None:
                        raise ValueError(f"Товар с ID {product_id} не найден")
                    if product.stock < item["quantity"]:
                        raise ValueError(f"Недостаточно товара: {product.name}")
                    product.stock -= item["quantity"]
                    order.items.append(OrderItem(
                        product_id=product.id, product_name=product.name,
                        quantity=item["quantity"], unit_price=Decimal(str(item["price"]))
                    ))
                session.commit()
                return order.id
            except Exception:
                session.rollback()
                raise
