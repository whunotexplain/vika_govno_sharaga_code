from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QMessageBox, QInputDialog
from DB_Units.order_repository import OrderRepository

class CartWindow(QDialog):
    def __init__(self, cart, on_change, parent=None):
        super().__init__(parent)
        self.cart, self.on_change = cart, on_change
        self.setWindowTitle("Корзина")
        self.resize(520, 400)
        layout = QVBoxLayout(self)
        self.items = QListWidget()
        layout.addWidget(self.items)
        buttons = QHBoxLayout()
        remove = QPushButton("Убрать выбранный")
        remove.clicked.connect(self.remove_selected)
        clear = QPushButton("Очистить")
        clear.clicked.connect(self.clear_cart)
        buttons.addWidget(remove)
        buttons.addWidget(clear)
        layout.addLayout(buttons)
        self.total_label = QLabel()
        layout.addWidget(self.total_label)
        checkout = QPushButton("Оформить заказ")
        checkout.clicked.connect(self.checkout)
        layout.addWidget(checkout)
        self.refresh()

    def refresh(self):
        self.items.clear()
        total = 0
        for item in self.cart.values():
            subtotal = item["price"] * item["quantity"]
            total += subtotal
            self.items.addItem(f'{item["name"]} — {item["price"]} ₽ × {item["quantity"]} = {subtotal:.2f} ₽')
        self.total_label.setText(f"Итого: {total:.2f} ₽")

    def remove_selected(self):
        index = self.items.currentRow()
        if index >= 0:
            del self.cart[list(self.cart)[index]]
            self.refresh()
            self.on_change()

    def clear_cart(self):
        self.cart.clear()
        self.refresh()
        self.on_change()

    def checkout(self):
        if not self.cart:
            QMessageBox.information(self, "Корзина", "Корзина пуста")
            return
        name, ok = QInputDialog.getText(self, "Заказ", "Имя покупателя:")
        if not ok or not name.strip():
            return
        try:
            order_id = OrderRepository.create(name.strip(), self.cart)
            self.cart.clear()
            self.refresh()
            self.on_change()
            QMessageBox.information(self, "Готово", f"Заказ №{order_id} оформлен")
        except Exception as error:
            QMessageBox.critical(self, "Ошибка", str(error))
