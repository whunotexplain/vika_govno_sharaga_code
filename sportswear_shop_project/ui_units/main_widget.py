from PyQt6.QtWidgets import *
from PyQt6 import QtCore, QtGui
from db_units.qwersql import QwerSql


class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.scroll_area_widget = QWidget()
        self.scroll_area_widget_layout = QVBoxLayout(self.scroll_area_widget)
        self.scroll_area_widget_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_area_widget)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.scroll_area)

    def clear_cards(self):
        while self.scroll_area_widget_layout.count():
            item = self.scroll_area_widget_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()


import os
from PyQt6.QtWidgets import *
from PyQt6 import QtCore, QtGui

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)


class NextWin(QWidget):
    def __init__(self, data):
        super().__init__()
        self.resize(360, 420)
        self.setWindowTitle("Информация о товаре")

        layout = QVBoxLayout(self)

        lbl_image = QLabel()
        lbl_image.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignCenter
        )

        image_path = data.get("img", "")

        if image_path and not os.path.isabs(image_path):
            image_path = os.path.join(BASE_DIR, image_path)

        pix = QtGui.QPixmap(image_path)

        if not pix.isNull():
            lbl_image.setPixmap(
                pix.scaled(
                    220, 220,
                    QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                    QtCore.Qt.TransformationMode.SmoothTransformation
                )
            )
        else:
            lbl_image.setText("Изображение отсутствует")
            print("Не найдено изображение:", image_path)

        layout.addWidget(lbl_image)

        text = (
            f"Название: {data['name']}\n"
            f"Категория: {data['category']}\n"
            f"Тип: {data['type']}\n"
            f"Бренд: {data['manufacturing']}\n"
            f"Материал: {data['cloth']}\n"
            f"Размер: {data['size']}\n"
            f"Цвет: {data['color']}\n"
            f"Количество: {data['quantity']}\n"
            f"Цена: {data['price']} ₽\n"
            f"Скидка: {data['discount']}%"
        )

        label = QLabel(text)
        label.setWordWrap(True)
        layout.addWidget(label)


class Auth(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Вход — SPORTWEAR")
        self.resize(420, 180)
        self.setModal(True)
        self.auth_data = None
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.le_login = QLineEdit()
        self.le_login.setPlaceholderText("Логин")
        self.le_passw = QLineEdit()
        self.le_passw.setPlaceholderText("Пароль")
        self.le_passw.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Логин:", self.le_login)
        form.addRow("Пароль:", self.le_passw)
        layout.addLayout(form)
        btn = QPushButton("Войти")
        btn.clicked.connect(self.show_page1)
        layout.addWidget(btn)
        layout.addWidget(QLabel("Демо-доступ: demo / demo123"))

    def show_page1(self):
        login, password = self.le_login.text().strip(), self.le_passw.text()
        if not login or not password:
            QMessageBox.warning(self, "Предупреждение", "Заполните все поля")
            return
        try:
            self.auth_data = QwerSql().get_auth(login, password)
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка БД", str(exc))
            return
        if self.auth_data:
            self.accept()
        else:
            QMessageBox.warning(self, "Предупреждение", "Неверный логин или пароль")


class AboutUserWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.main_layout = QVBoxLayout(self)
        self.form_about_user = QFormLayout()
        self.lb_photo = QLabel("Фото профиля")
        self.lb_photo.setFixedSize(160, 120)
        self.lb_photo.setStyleSheet("border: 1px solid gray;")
        self.lb_photo.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.form_about_user.addRow("Фото", self.lb_photo)
        self.le_name, self.le_surname = QLineEdit(), QLineEdit()
        self.le_email, self.le_phone = QLineEdit(), QLineEdit()
        self.form_about_user.addRow("Имя", self.le_name)
        self.form_about_user.addRow("Фамилия", self.le_surname)
        self.form_about_user.addRow("Почта", self.le_email)
        self.form_about_user.addRow("Телефон", self.le_phone)
        self.main_layout.addLayout(self.form_about_user)
        buttons = QHBoxLayout()
        self.bt_edit_pass = QPushButton("Изменить пароль")
        self.bt_edit_user_data = QPushButton("Редактировать данные")
        buttons.addWidget(self.bt_edit_user_data)
        buttons.addWidget(self.bt_edit_pass)
        self.main_layout.addLayout(buttons)
        self.bt_user_data_save = QPushButton("Сохранить")
        self.bt_user_data_save.hide()
        self.main_layout.addWidget(self.bt_user_data_save)
        self.main_layout.addStretch()


class PassEditDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Смена пароля")
        self.setModal(True)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.old_pass, self.new1_pass, self.new2_pass = QLineEdit(), QLineEdit(), QLineEdit()
        for field in (self.old_pass, self.new1_pass, self.new2_pass):
            field.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Старый пароль", self.old_pass)
        form.addRow("Новый пароль", self.new1_pass)
        form.addRow("Повторите новый пароль", self.new2_pass)
        self.bt_save_pass = QPushButton("Сохранить")
        layout.addLayout(form)
        layout.addWidget(self.bt_save_pass)
