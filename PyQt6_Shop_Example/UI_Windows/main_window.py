from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QDoubleSpinBox, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QAbstractItemView
)
from UI_Windows.product_details_window import ProductDetailsWindow
from UI_Windows.cart_window import CartWindow
from DB_Units.product_repository import ProductRepository

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 Shop Example")
        self.resize(1050, 650)
        self.cart, self.products = {}, []
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.addWidget(QLabel("<h1>Магазин электроники</h1>"))

        filters = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск по названию...")
        self.category = QComboBox()
        self.category.addItem("Все")
        self.category.addItems(ProductRepository.categories())
        self.minimum, self.maximum = QDoubleSpinBox(), QDoubleSpinBox()
        self.minimum.setPrefix("От ")
        self.maximum.setPrefix("До ")
        for spin in (self.minimum, self.maximum):
            spin.setMaximum(1_000_000)
        self.maximum.setValue(1_000_000)
        self.sort = QComboBox()
        self.sort.addItems(["Название", "Цена: по возрастанию", "Цена: по убыванию"])
        for widget in (self.search, self.category, self.minimum, self.maximum, self.sort):
            filters.addWidget(widget)
        root.addLayout(filters)
        self.search.textChanged.connect(self.refresh_products)
        self.category.currentTextChanged.connect(self.refresh_products)
        self.minimum.valueChanged.connect(self.refresh_products)
        self.maximum.valueChanged.connect(self.refresh_products)
        self.sort.currentTextChanged.connect(self.refresh_products)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Название", "Категория", "Цена, ₽", "Остаток"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self.show_details)
        root.addWidget(self.table)

        actions = QHBoxLayout()
        for title, callback in [
            ("Подробнее", self.show_details), ("В корзину", self.add_to_cart),
            ("Корзина / заказ", self.open_cart), ("Обновить", self.refresh_products)
        ]:
            button = QPushButton(title)
            button.clicked.connect(callback)
            actions.addWidget(button)
        root.addLayout(actions)
        self.refresh_products()

    def refresh_products(self):
        self.products = ProductRepository.get_all(
            self.search.text(), self.category.currentText(),
            self.minimum.value(), self.maximum.value(), self.sort.currentText()
        )
        self.table.setRowCount(len(self.products))
        for row, product in enumerate(self.products):
            values = [product.id, product.name, product.category, f"{product.price:.2f}", product.stock]
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(str(value)))
        self.table.resizeColumnsToContents()
        self.statusBar().showMessage(f"Найдено товаров: {len(self.products)}")

    def selected_product(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Товар", "Выбери товар в таблице")
            return None
        return self.products[row]

    def show_details(self):
        product = self.selected_product()
        if product:
            ProductDetailsWindow(product, self).exec()

    def add_to_cart(self):
        product = self.selected_product()
        if not product:
            return
        item = self.cart.setdefault(product.id, {"name": product.name, "price": float(product.price), "quantity": 0})
        if item["quantity"] >= product.stock:
            QMessageBox.warning(self, "Остаток", "Недостаточно товара на складе")
            return
        item["quantity"] += 1
        self.statusBar().showMessage(f"Добавлено: {product.name}", 3000)

    def open_cart(self):
        CartWindow(self.cart, self.refresh_products, self).exec()
        self.refresh_products()
