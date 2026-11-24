from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton

class ProductDetailsWindow(QDialog):
    def __init__(self, product, parent=None):
        super().__init__(parent)
        self.setWindowTitle(product.name)
        self.setMinimumWidth(360)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<h2>{product.name}</h2>"))
        for text in (
            f"Категория: {product.category}",
            f"Цена: {product.price} ₽",
            f"Остаток: {product.stock} шт.",
            product.description or "Описание отсутствует",
        ):
            label = QLabel(text)
            label.setWordWrap(True)
            layout.addWidget(label)
        button = QPushButton("Закрыть")
        button.clicked.connect(self.accept)
        layout.addWidget(button)
