from PyQt6.QtWidgets import *
from PyQt6 import QtCore, QtGui
from db_units.qwersql import QwerSql
from ui_units.main_widget import MainWidget, NextWin, Auth, AboutUserWidget, PassEditDialog
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class MyWin(QMainWindow):
    def __init__(self, user_id=0):
        super().__init__()
        self.user_id = user_id
        self.current_page = 0
        self.db = QwerSql()
        self.total_pages = self.db.total_pages()

        self.setWindowTitle("Магазин спортивной одежды")
        self.setWindowIcon(QtGui.QIcon("resources/images.jpeg"))
        self.resize(900, 600)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        header = QHBoxLayout()
        title = QLabel("SPORTWEAR — спортивная одежда")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        self.btn_login = QPushButton("Войти")
        self.btn_login.clicked.connect(self.entry_win)
        header.addWidget(self.btn_login)
        main_layout.addLayout(header)

        self.main_widget = MainWidget()
        main_layout.addWidget(self.main_widget, 1)

        self.wid_about_user = AboutUserWidget()
        self.wid_about_user.hide()
        main_layout.addWidget(self.wid_about_user)

        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)
        menu_user = self.menu_bar.addMenu("Личный кабинет")
        menu_user.addAction("О пользователе", self.about_user_triggered)
        menu_user.addAction("Каталог", self.show_catalog)
        menu_user.addAction("Выйти", self.on_logout)
        self.menu_bar.hide()

        bottom = QHBoxLayout()
        self.btn_prev = QPushButton("← Назад")
        self.btn_next = QPushButton("Вперёд →")
        self.btn_prev.clicked.connect(self.prev_page)
        self.btn_next.clicked.connect(self.next_page)
        bottom.addWidget(self.btn_prev)
        bottom.addStretch()
        bottom.addWidget(self.btn_next)
        main_layout.addLayout(bottom)

        self.wid_about_user.bt_edit_user_data.clicked.connect(self.edit_user_data)
        self.wid_about_user.bt_user_data_save.clicked.connect(self.edit_user_data)
        self.wid_about_user.bt_edit_pass.clicked.connect(self.edit_user_pass)
        self.render_page()

    def closeEvent(self, event):
        self.db.close()
        super().closeEvent(event)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.render_page()

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.render_page()

    def render_page(self):
        self.main_widget.clear_cards()
        self.total_pages = self.db.total_pages()
        for row in self.db.show_products(self.current_page):
            (product_id, name, category, type_, brand, material, size, color,
             quantity, price, discount, image_path) = row
            data = {
                "img": image_path or "",
                "name": name, "category": category, "type": type_,
                "manufacturing": brand, "cloth": material or "Не указан",
                "size": size, "color": color, "quantity": quantity,
                "price": price, "discount": discount,
            }
            self.add_cards(data)
        self.btn_prev.setEnabled(self.current_page > 0)
        self.btn_next.setEnabled(self.current_page < self.total_pages - 1)

    def add_cards(self, data):
        card = QWidget()
        layout = QHBoxLayout(card)
        image = QLabel()
        image_path = data["img"]

        if image_path and not os.path.isabs(image_path):
            image_path = os.path.join(BASE_DIR, image_path)

        pix = QtGui.QPixmap(image_path)
        print("Путь к фото:", image_path)
        print("Файл существует:", os.path.exists(image_path))
        print("Фото загружено:", not pix.isNull())
        if not pix.isNull():
            image.setPixmap(pix.scaled(110, 110, QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                                       QtCore.Qt.TransformationMode.SmoothTransformation))
        else:
            image.setText("Нет фото")
            image.setFixedSize(110, 110)
            image.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        image.setFrameStyle(QFrame.Shape.Box)
        text = QLabel(
            f"<b>{data['name']}</b><br>{data['category']} · {data['manufacturing']}<br>"
            f"Размер: {data['size']} · Цвет: {data['color']}<br>"
            f"В наличии: {data['quantity']} · Цена: {data['price']} ₽"
        )
        text.setTextFormat(QtCore.Qt.TextFormat.RichText)
        text.setWordWrap(True)
        text.mousePressEvent = lambda event, d=data: self.open_details(d)
        text.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        discount = QLabel(f"−{data['discount']}%")
        discount.setStyleSheet("font-weight: bold; color: #c0392b;")
        layout.addWidget(image)
        layout.addWidget(text, 1)
        layout.addWidget(discount)
        self.main_widget.scroll_area_widget_layout.addWidget(card)

    def open_details(self, data):
        self.next_win = NextWin(data)
        self.next_win.show()

    def entry_win(self):
        dialog = Auth()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.user_id = dialog.auth_data["id"]
            self.menu_bar.show()
            self.btn_login.hide()

    def on_logout(self):
        self.menu_bar.hide()
        self.btn_login.show()
        self.show_catalog()

    def show_catalog(self):
        self.wid_about_user.hide()
        self.main_widget.show()
        self.btn_prev.show()
        self.btn_next.show()
        self.render_page()

    def about_user_triggered(self):
        if not self.user_id:
            QMessageBox.information(self, "Личный кабинет", "Сначала войдите в аккаунт.")
            return
        self.main_widget.hide()
        self.btn_prev.hide()
        self.btn_next.hide()
        self.wid_about_user.show()
        info = self.db.get_user_info(self.user_id)
        if info:
            for key, widget in (("fname", self.wid_about_user.le_name),
                                ("lname", self.wid_about_user.le_surname),
                                ("email", self.wid_about_user.le_email),
                                ("phone", self.wid_about_user.le_phone)):
                widget.setText(info[key])
                widget.setEnabled(False)

    def edit_user_data(self):
        w = self.wid_about_user
        if not w.le_name.isEnabled():
            for field in (w.le_name, w.le_surname, w.le_email, w.le_phone):
                field.setEnabled(True)
            w.bt_edit_user_data.hide()
            w.bt_user_data_save.show()
        else:
            try:
                self.db.set_new_user_data(
                    w.le_name.text().strip(), w.le_surname.text().strip(),
                    w.le_email.text().strip(), w.le_phone.text().strip(), self.user_id
                )
            except Exception as exc:
                self.db.conn.rollback()
                QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить данные: {exc}")
                return
            for field in (w.le_name, w.le_surname, w.le_email, w.le_phone):
                field.setEnabled(False)
            w.bt_edit_user_data.show()
            w.bt_user_data_save.hide()
            QMessageBox.information(self, "Успешно", "Данные сохранены.")

    def edit_user_pass(self):
        self.dialog_edit_pass = PassEditDialog()
        self.dialog_edit_pass.bt_save_pass.clicked.connect(self.save_user_pass)
        self.dialog_edit_pass.exec()

    def save_user_pass(self):
        d = self.dialog_edit_pass
        old_p, new1, new2 = d.old_pass.text(), d.new1_pass.text(), d.new2_pass.text()
        if not old_p or not new1 or not new2:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return
        if new1 != new2:
            QMessageBox.warning(self, "Ошибка", "Новые пароли не совпадают")
            return
        if not self.db.verify_password(self.user_id, old_p):
            QMessageBox.warning(self, "Ошибка", "Неверный старый пароль")
            return
        self.db.update_password(self.user_id, new1)
        QMessageBox.information(self, "Успешно", "Пароль изменён")
        d.accept()
