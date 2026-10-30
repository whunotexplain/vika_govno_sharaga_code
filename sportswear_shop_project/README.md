# Подробный учебник по PyQt6 + PostgreSQL: как писать приложение на контрольной

> Цель — научиться не копировать готовый проект, а понимать, как связаны кнопки, методы, SQL и данные. Это руководство разбирает именно структуру проекта магазина спортивной одежды и даёт шаблоны, которые можно адаптировать под товары, студентов, книги, сотрудников и другие системы учёта.

## 0. Главная идея: как работает приложение

Почти любое задание можно разделить на четыре части:

1. **База данных** — хранит информацию.
2. **Класс Database** — подключается к PostgreSQL и выполняет SQL.
3. **Графический интерфейс (UI)** — окна, кнопки, поля, таблицы.
4. **Методы главного окна** — связывают действия пользователя с методами базы.

Запомни главную цепочку:

~~~text
Пользователь нажал кнопку
          |
          v
button.clicked.connect(self.add_record)
          |
          v
Метод add_record() в главном окне
  1. читает значения полей
  2. проверяет их
  3. вызывает метод БД
          |
          v
self.db.add_record(...)
          |
          v
SQL INSERT в PostgreSQL
          |
          v
commit() сохраняет изменения
          |
          v
load_data() заново загружает данные в таблицу
~~~

**Кнопка не должна сама выполнять SQL.** Она запускает метод интерфейса. Метод интерфейса получает значения полей и вызывает метод класса БД. Класс БД выполняет запрос.

Универсальный алгоритм обработчика: **ПОЛУЧИТЬ → ПРОВЕРИТЬ → ВЫЗВАТЬ БД → СООБЩИТЬ → ОБНОВИТЬ.**

---

## 1. Структура проекта: кто за что отвечает

~~~text
sportswear_shop_project/
│
├── main.py                    # запуск приложения
├── texshopProductShow.py      # главное окно и связь UI с БД
├── schema.sql                 # таблицы, связи, тестовые данные
├── requirements.txt           # библиотеки Python
├── .env                       # настройки подключения, не публиковать!
│
├── db_units/
│   └── qwersql.py             # подключение и SQL-запросы
│
├── ui_units/
│   └── main_widget.py         # отдельные виджеты и диалоговые окна
│
└── resources/
    └── images/                # изображения товаров
~~~

| Файл | Назначение |
|---|---|
| main.py | Создаёт QApplication и главное окно |
| texshopProductShow.py | Реагирует на действия пользователя, вызывает методы БД |
| db_units/qwersql.py | Подключение, SELECT, INSERT, UPDATE, DELETE |
| ui_units/main_widget.py | Создание виджетов, форм и диалогов |
| schema.sql | Создание таблиц, ключей, ограничений и представлений |

Главное правило разделения: **UI не должен содержать SQL, а файл БД не должен создавать кнопки.**

Для маленькой контрольной преподаватель может разрешить всё написать в одном файле. Даже тогда мысленно разделяй интерфейс и работу с данными.

---

## 2. Запуск приложения: main.py

~~~python
import sys
from PyQt6.QtWidgets import QApplication
from texshopProductShow import MyWin

if __name__ == "__main__":
    app = QApplication(sys.argv)  # создаём приложение Qt
    window = MyWin()              # создаём главное окно
    window.show()                 # показываем окно
    sys.exit(app.exec())          # запускаем цикл событий
~~~

Разбор:

- **QApplication** — обязательный объект Qt. Управляет окнами и событиями.
- **MyWin()** — создаёт объект нашего главного окна.
- **show()** — делает окно видимым.
- **app.exec()** — запускает цикл событий: приложение ждёт клики, ввод текста и закрытие окна.
- **sys.exit()** — корректно завершает процесс.

Почему нельзя просто создать окно и закончить программу? Python дойдёт до конца файла и завершит процесс. Цикл событий удерживает приложение запущенным.

---

## 3. Главное окно: базовый шаблон

~~~python
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Моё приложение")
        self.resize(900, 600)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        self.label = QLabel("Добро пожаловать")
        self.btn = QPushButton("Нажми меня")

        layout.addWidget(self.label)
        layout.addWidget(self.btn)

        self.btn.clicked.connect(self.on_click)

    def on_click(self):
        self.label.setText("Кнопка нажата!")
~~~

### Объяснение каждой важной строки

- **class MainWindow(QMainWindow)** — создаём собственный класс на основе готового класса Qt.
- **def __init__(self)** — конструктор, запускается при создании объекта.
- **super().__init__()** — инициализирует родительский класс Qt. Почти всегда нужен в начале конструктора.
- **self.label** — атрибут объекта. Он доступен из других методов этого же окна.
- **QWidget()** — обычный виджет-контейнер.
- **setCentralWidget()** — задаёт центральную область QMainWindow.
- **QVBoxLayout()** — располагает элементы вертикально.
- **addWidget()** — добавляет виджет в layout.
- **clicked.connect()** — связывает сигнал кнопки с методом.

Почему пишем self.btn, а не просто btn? Локальная переменная btn доступна только внутри __init__. Атрибут self.btn принадлежит объекту окна и доступен в других методах.

### Основные layout

| Layout | Расположение | Где удобно |
|---|---|---|
| QVBoxLayout | Сверху вниз | Поля формы друг под другом |
| QHBoxLayout | Слева направо | Кнопки в одну строку |
| QGridLayout | Сетка строк и столбцов | Сложная форма |
| QFormLayout | Подпись + поле | Авторизация и анкеты |

Пример горизонтальной панели:

~~~python
top_layout = QHBoxLayout()
top_layout.addWidget(QLabel("Каталог"))
top_layout.addStretch()
top_layout.addWidget(QPushButton("Войти"))
main_layout.addLayout(top_layout)
~~~

addStretch() создаёт свободное растягиваемое место и отодвигает кнопку вправо.

---

## 4. САМОЕ ВАЖНОЕ: сигнал кнопки вызывает метод

PyQt работает по событийной модели. Программа не выполняет все методы подряд. Она ждёт событие: клик, ввод текста, выбор строки, закрытие окна.

### Сигнал и слот

~~~python
self.btn_save.clicked.connect(self.save_data)
~~~

- **clicked** — сигнал. Qt отправляет его, когда кнопку нажали.
- **connect()** — соединяет сигнал с обработчиком.
- **self.save_data** — метод, который будет вызван.

Важно: передаём метод **без скобок**.

Правильно:

~~~python
self.btn_save.clicked.connect(self.save_data)
~~~

Неправильно:

~~~python
self.btn_save.clicked.connect(self.save_data())
~~~

Во втором случае Python выполнит метод сразу при создании окна, а не после клика.

### Полный путь: поле → метод → БД → интерфейс

Допустим, пользователь вводит название товара и нажимает «Добавить».

**Шаг 1. Создаём поле и кнопку.**

~~~python
self.le_name = QLineEdit()
self.btn_add = QPushButton("Добавить")

layout.addWidget(self.le_name)
layout.addWidget(self.btn_add)
~~~

**Шаг 2. Соединяем кнопку с методом.**

~~~python
self.btn_add.clicked.connect(self.add_product)
~~~

**Шаг 3. Метод получает текст из поля.**

~~~python
def add_product(self):
    name = self.le_name.text().strip()
~~~

text() получает текст. strip() удаляет пробелы по краям.

**Шаг 4. Проверяем ввод.**

~~~python
if not name:
    QMessageBox.warning(self, "Ошибка", "Введите название")
    return
~~~

return прекращает выполнение метода. Пустое название не попадёт в БД.

**Шаг 5. Вызываем метод базы.**

~~~python
self.db.add_product(name)
~~~

**Шаг 6. Показываем результат и обновляем данные.**

~~~python
QMessageBox.information(self, "Успех", "Товар добавлен")
self.load_products()
~~~

Полный обработчик:

~~~python
def add_product(self):
    name = self.le_name.text().strip()

    if not name:
        QMessageBox.warning(self, "Ошибка", "Введите название")
        return

    try:
        self.db.add_product(name)
        QMessageBox.information(self, "Успех", "Товар добавлен")
        self.le_name.clear()
        self.load_products()
    except Exception as exc:
        QMessageBox.critical(self, "Ошибка", str(exc))
~~~

**Это центральный шаблон всей контрольной.** Меняются названия полей и вызываемый метод, но последовательность остаётся прежней.

### Как передать данные в другое окно

В проекте карточка товара открывается так:

~~~python
def open_details(self, data):
    self.next_win = NextWin(data)
    self.next_win.show()
~~~

Новое окно принимает данные:

~~~python
class NextWin(QWidget):
    def __init__(self, data):
        super().__init__()
        label = QLabel(data["name"])
~~~

То есть главное окно передаёт словарь в конструктор другого окна. Новое окно получает его через аргумент data и обращается к значениям по ключам.

---

## 5. Подключение PostgreSQL: класс БД

В проекте используется библиотека psycopg2.

Минимальное подключение:

~~~python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port="5432",
    dbname="my_database",
    user="postgres",
    password="your_password"
)
cur = conn.cursor()
~~~

- connect() — открывает соединение с базой.
- conn — объект соединения, через него управляют транзакциями.
- cursor() — создаёт курсор для SQL.
- cur.execute() — выполняет запрос.

Обычно это оформляют классом:

~~~python
import psycopg2

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            host="localhost",
            dbname="my_database",
            user="postgres",
            password="1234"
        )
        self.cur = self.conn.cursor()
~~~

Почему self.conn и self.cur? Чтобы все методы класса могли использовать уже созданные соединение и курсор.

### 5.1. SELECT — получить данные

~~~python
def get_products(self):
    self.cur.execute(
        "SELECT id, name, price FROM products ORDER BY id"
    )
    return self.cur.fetchall()
~~~

fetchall() возвращает список строк. Например:

~~~python
[
    (1, "Футболка", 1290.00),
    (2, "Кроссовки", 5990.00)
]
~~~

Одна запись — кортеж. Поэтому можно обращаться по индексам:

~~~python
rows = self.db.get_products()

for row in rows:
    product_id = row[0]
    name = row[1]
    price = row[2]
~~~

| Метод | Результат |
|---|---|
| fetchone() | Одна строка или None |
| fetchall() | Все строки списком |
| fetchmany(5) | До пяти строк |

### 5.2. Параметры SQL: используй %s

Если значение пришло от пользователя, не собирай SQL через f-строку.

Плохо:

~~~python
sql = f"SELECT * FROM client WHERE login = '{login}'"
self.cur.execute(sql)
~~~

Правильно:

~~~python
self.cur.execute(
    "SELECT * FROM client WHERE login = %s",
    (login,)
)
~~~

Два параметра:

~~~python
self.cur.execute(
    "SELECT id FROM client WHERE login = %s AND password = %s",
    (login, password)
)
~~~

Запомни:
- Для psycopg2 используется %s, а не ?.
- Значения передаются вторым аргументом.
- Один параметр — кортеж с запятой: (value,).
- Два параметра — (value1, value2).

Так драйвер корректно передаёт значения и защищает от SQL-инъекций.

### 5.3. INSERT — добавить запись

~~~python
def add_product(self, name, price):
    self.cur.execute(
        "INSERT INTO products (name, price) VALUES (%s, %s)",
        (name, price)
    )
    self.conn.commit()
~~~

commit() фиксирует изменения. Без него INSERT/UPDATE/DELETE могут не сохраниться.

Если нужно получить ID новой записи:

~~~python
self.cur.execute(
    "INSERT INTO products (name, price) VALUES (%s, %s) RETURNING id",
    (name, price)
)
new_id = self.cur.fetchone()[0]
self.conn.commit()
return new_id
~~~

### 5.4. UPDATE — изменить запись

~~~python
def update_product(self, name, price, product_id):
    self.cur.execute(
        "UPDATE products SET name = %s, price = %s WHERE id = %s",
        (name, price, product_id)
    )
    self.conn.commit()
~~~

**Без WHERE id = %s изменятся все строки таблицы!**

### 5.5. DELETE — удалить запись

~~~python
def delete_product(self, product_id):
    self.cur.execute(
        "DELETE FROM products WHERE id = %s",
        (product_id,)
    )
    self.conn.commit()
~~~

Перед удалением желательно спросить подтверждение:

~~~python
answer = QMessageBox.question(self, "Подтверждение", "Удалить запись?")
if answer == QMessageBox.StandardButton.Yes:
    self.db.delete_product(product_id)
    self.load_products()
~~~

### 5.6. commit, rollback, close

~~~python
try:
    self.cur.execute("UPDATE products SET name = %s WHERE id = %s",
                     (name, product_id))
    self.conn.commit()
except Exception:
    self.conn.rollback()
    raise
~~~

- **commit()** — сохранить изменения.
- **rollback()** — отменить изменения текущей транзакции после ошибки.
- **close()** — закрыть курсор или соединение.

Закрытие:

~~~python
def close(self):
    self.cur.close()
    self.conn.close()
~~~

В главном окне:

~~~python
def closeEvent(self, event):
    self.db.close()
    super().closeEvent(event)
~~~

---

## 6. CRUD — четыре операции почти любой контрольной

CRUD означает Create, Read, Update, Delete.

| Операция | SQL | Метод БД | Что делает интерфейс |
|---|---|---|---|
| Create | INSERT | add_product(...) | Читает поля и вызывает INSERT |
| Read | SELECT | get_products() | Получает строки и показывает |
| Update | UPDATE | update_product(...) | Берёт ID выбранной строки и новые значения |
| Delete | DELETE | delete_product(id) | Берёт ID, подтверждает удаление |

Универсальный класс:

~~~python
class Database:
    def __init__(self):
        self.conn = psycopg2.connect(...)
        self.cur = self.conn.cursor()

    # READ
    def get_all(self):
        self.cur.execute("SELECT id, name FROM products ORDER BY id")
        return self.cur.fetchall()

    # CREATE
    def add(self, name):
        self.cur.execute(
            "INSERT INTO products (name) VALUES (%s)", (name,)
        )
        self.conn.commit()

    # UPDATE
    def update(self, product_id, name):
        self.cur.execute(
            "UPDATE products SET name = %s WHERE id = %s",
            (name, product_id)
        )
        self.conn.commit()

    # DELETE
    def delete(self, product_id):
        self.cur.execute(
            "DELETE FROM products WHERE id = %s", (product_id,)
        )
        self.conn.commit()
~~~

Для другого задания меняются таблица, поля и названия методов. Скелет остаётся тем же.

---

## 7. Вывод данных в интерфейс

### 7.1. Через QLabel

~~~python
rows = self.db.get_products()

for row in rows:
    label = QLabel(f"{row[1]} — {row[2]} ₽")
    layout.addWidget(label)
~~~

Подходит для простого списка или карточек.

### 7.2. Через QTableWidget

Создаём таблицу:

~~~python
self.table = QTableWidget()
self.table.setColumnCount(3)
self.table.setHorizontalHeaderLabels(["ID", "Название", "Цена"])
layout.addWidget(self.table)
~~~

Заполняем:

~~~python
def load_products(self):
    rows = self.db.get_products()
    self.table.setRowCount(len(rows))

    for row_index, row in enumerate(rows):
        for col_index, value in enumerate(row):
            item = QTableWidgetItem(str(value))
            self.table.setItem(row_index, col_index, item)
~~~

Построчно:
1. get_products() получает список кортежей из БД.
2. setRowCount(len(rows)) задаёт количество строк.
3. enumerate(rows) даёт индекс и содержимое строки.
4. Внутренний цикл перебирает значения кортежа.
5. QTableWidgetItem(str(value)) создаёт ячейку. В таблицу передаём строку.
6. setItem(row, column, item) помещает ячейку в таблицу.

### 7.3. Как получить ID выбранной строки

Это ключевой момент для UPDATE и DELETE.

Если ID находится в первом столбце:

~~~python
def get_selected_id(self):
    row = self.table.currentRow()

    if row < 0:
        QMessageBox.warning(self, "Ошибка", "Выберите запись")
        return None

    return int(self.table.item(row, 0).text())
~~~

Использование:

~~~python
def delete_selected(self):
    product_id = self.get_selected_id()

    if product_id is None:
        return

    self.db.delete_product(product_id)
    self.load_products()
~~~

**Не путай номер строки и ID!** Номер строки — позиция на экране. ID — первичный ключ записи в БД. После сортировки или фильтрации они могут различаться.

---

## 8. Поля ввода: как получать значения

| Виджет | Назначение | Получение значения |
|---|---|---|
| QLineEdit | Однострочный текст | text() |
| QTextEdit | Большой текст | toPlainText() |
| QSpinBox | Целое число | value() |
| QDoubleSpinBox | Дробное число | value() |
| QComboBox | Выбор из списка | currentText() |
| QCheckBox | Да/нет | isChecked() |
| QDateEdit | Дата | date() |

Пример создания:

~~~python
self.le_name = QLineEdit()
self.sb_quantity = QSpinBox()
self.sb_price = QDoubleSpinBox()
self.cb_category = QComboBox()

self.cb_category.addItems(["Футболки", "Обувь", "Куртки"])
~~~

Получение:

~~~python
name = self.le_name.text().strip()
quantity = self.sb_quantity.value()
price = self.sb_price.value()
category = self.cb_category.currentText()
~~~

QLineEdit возвращает строку. Если вводишь число через него, преобразуй:

~~~python
price = float(self.le_price.text())
quantity = int(self.le_quantity.text())
~~~

Если используешь QSpinBox или QDoubleSpinBox, преобразование не нужно: value() уже возвращает число.

---

## 9. Как главное окно использует класс БД

В главном окне:

~~~python
class MyWin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = QwerSql()
~~~

При создании главного окна создаётся объект БД. Теперь любой метод окна может обращаться к нему:

~~~python
def render_page(self):
    rows = self.db.show_products(self.current_page)
~~~

- self.db — объект доступа к базе.
- show_products — метод объекта.
- self.current_page — номер страницы.
- rows — результат SELECT.

Почему не писать SQL прямо в обработчике кнопки? Потому что запросы будут разбросаны по интерфейсу. Если SQL находится в классе БД, его проще проверять, исправлять и повторно использовать.

---

## 10. Разбор конкретного магазина из репозитория

### 10.1. Таблицы и связи

В schema.sql созданы:

- client — пользователи;
- categories — категории;
- products — товары;
- orders — заказы;
- order_items — позиции заказа.

Связи:

~~~text
categories (1) -------- (М) products
client     (1) -------- (М) orders
orders     (1) -------- (М) order_items
products   (1) -------- (М) order_items
~~~

Одна категория может включать много товаров. Поле products.category_id — внешний ключ на categories.id:

~~~sql
category_id BIGINT NOT NULL REFERENCES categories(id)
~~~

Это не позволяет создать товар с несуществующей категорией.

### 10.2. Представление v_products_full

В базе создано VIEW:

~~~sql
CREATE OR REPLACE VIEW v_products_full AS
SELECT p.id, p.name, c.name AS category, p.product_type, p.brand,
       p.material, p.size, p.color, p.quantity, p.price, p.discount,
       p.image_path
FROM products p
JOIN categories c ON c.id = p.category_id
WHERE p.is_active = TRUE;
~~~

Таблица хранит данные, а представление — сохранённый SQL-запрос, который выглядит как виртуальная таблица.

Здесь в products хранится category_id, но пользователю нужно видеть название категории. JOIN соединяет товар с категорией, а WHERE скрывает неактивные товары.

### 10.3. Пагинация — страницы каталога

В классе БД:

~~~python
PAGE_SIZE = 4

def total_pages(self):
    total = self.count_products()
    return max(1, (total + self.PAGE_SIZE - 1) // self.PAGE_SIZE)

def show_products(self, page=0):
    offset = self.PAGE_SIZE * max(0, page)
    self.cur.execute(
        """SELECT id, name, category, product_type, brand, material,
                  size, color, quantity, price, discount, image_path
           FROM v_products_full
           ORDER BY id LIMIT %s OFFSET %s""",
        (self.PAGE_SIZE, offset)
    )
    return self.cur.fetchall()
~~~

- LIMIT 4 — максимум 4 товара на странице.
- OFFSET 0 — начать с первой записи.
- На второй странице OFFSET 4, на третьей OFFSET 8.
- PAGE_SIZE — размер страницы.

Формула: offset = page * PAGE_SIZE.

В главном окне:

~~~python
def next_page(self):
    if self.current_page < self.total_pages - 1:
        self.current_page += 1
        self.render_page()

def prev_page(self):
    if self.current_page > 0:
        self.current_page -= 1
        self.render_page()
~~~

Проверки не дают уйти дальше последней страницы или на отрицательную.

### 10.4. Как кортеж из SQL превращается в карточку

В render_page() код получает строки из БД и собирает словарь:

~~~python
for row in self.db.show_products(self.current_page):
    (product_id, name, category, type_, brand, material, size, color,
     quantity, price, discount, image_path) = row

    data = {
        "img": image_path or "",
        "name": name,
        "category": category,
        "type": type_,
        "manufacturing": brand,
        "cloth": material or "Не указан",
        "size": size,
        "color": color,
        "quantity": quantity,
        "price": price,
        "discount": discount,
    }
    self.add_cards(data)
~~~

Почему словарь удобен? В кортеже приходится помнить индексы row[1], row[2]. В словаре можно написать data["name"], data["price"]. В add_cards передаётся один объект со всеми данными.

Затем add_cards(data) создаёт виджеты карточки и показывает название, цену, размер и цвет.

### 10.5. Авторизация: путь данных

Виджет Auth содержит поля логина и пароля. Кнопка подключена к методу:

~~~python
btn.clicked.connect(self.show_page1)
~~~

Метод:
1. получает логин и пароль через text();
2. проверяет, что поля не пустые;
3. вызывает QwerSql().get_auth(login, password);
4. если пользователь найден — вызывает accept();
5. если нет — показывает предупреждение.

QDialog может завершиться с результатом:
- Accepted — действие подтверждено;
- Rejected — диалог отменён.

Главное окно открывает диалог:

~~~python
dialog = Auth()
if dialog.exec() == QDialog.DialogCode.Accepted:
    self.user_id = dialog.auth_data["id"]
    self.menu_bar.show()
~~~

ID вошедшего пользователя сохраняется в главном окне. Затем он используется для получения профиля.

Важно: в учебном примере пароль хранится открытым текстом. В реальном приложении так делать нельзя — нужно хранить хэш пароля. Также в Auth создаётся отдельное соединение БД, которое лучше корректно закрывать или передавать в диалог уже созданный объект БД.

### 10.6. Личный кабинет

Метод about_user_triggered():
1. проверяет self.user_id;
2. если пользователь не вошёл — показывает сообщение и делает return;
3. скрывает каталог и пагинацию;
4. показывает виджет профиля;
5. получает данные через self.db.get_user_info(self.user_id);
6. устанавливает значения в поля через setText().

Из Python в поле:

~~~python
self.wid_about_user.le_name.setText(info["fname"])
~~~

Из поля в Python:

~~~python
name = self.wid_about_user.le_name.text()
~~~

### 10.7. Редактирование профиля

В текущем проекте метод переключает два режима:
- если поля заблокированы — разрешает редактирование;
- если поля доступны — сохраняет данные.

~~~python
if not w.le_name.isEnabled():
    # режим редактирования
    w.le_name.setEnabled(True)
else:
    # режим сохранения
    self.db.set_new_user_data(...)
~~~

- setEnabled(True) — разрешить редактирование.
- setEnabled(False) — заблокировать.
- hide() — скрыть.
- show() — показать.

Для контрольной иногда проще сделать два отдельных метода: enable_edit() и save_data(). Но важно понимать логику if/else.

---

## 11. Как написать приложение с нуля на контрольной

Делай по этапам. Не начинай с дизайна.

### Этап 1. Выпиши сущность и поля

Например, задание «учёт товаров»:
- таблица products;
- поля id, name, price, quantity;
- первичный ключ id.

### Этап 2. Создай таблицу

~~~sql
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0
);
~~~

### Этап 3. Напиши подключение

~~~python
import psycopg2

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            host="localhost",
            dbname="my_database",
            user="postgres",
            password="1234"
        )
        self.cur = self.conn.cursor()
~~~

### Этап 4. Напиши SELECT и проверь его

~~~python
def get_products(self):
    self.cur.execute("SELECT id, name, price, quantity FROM products")
    return self.cur.fetchall()
~~~

### Этап 5. Создай окно и таблицу

Создай QMainWindow, центральный QWidget, layout, QTableWidget и кнопки.

### Этап 6. Напиши загрузку таблицы

~~~python
def load_products(self):
    rows = self.db.get_products()
    self.table.setRowCount(len(rows))

    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            self.table.setItem(i, j, QTableWidgetItem(str(value)))
~~~

Вызови load_products() в конце __init__, чтобы таблица заполнилась при запуске.

### Этап 7. Добавь кнопку и обработчик

~~~python
self.btn_add.clicked.connect(self.add_product)
~~~

Затем напиши add_product(): прочитать поля → проверить → вызвать self.db.add_product(...) → вызвать self.load_products().

### Этап 8. Добавь изменение и удаление

Для изменения и удаления сначала получи ID выбранной строки. Не используй номер строки как ID.

### Этап 9. Добавь проверки

Проверь пустые поля, формат чисел, выбранную строку, ошибки SQL и успешное сохранение.

### Этап 10. Протестируй сценарий

1. Запустить программу.
2. Убедиться, что данные загрузились.
3. Добавить запись.
4. Проверить, что она появилась.
5. Изменить запись.
6. Убедиться, что изменилась нужная запись.
7. Удалить запись.
8. Перезапустить программу и убедиться, что данные остались в БД.

---

## 12. Компактный шаблон CRUD-окна

Предполагается, что класс Database имеет методы get_all(), add(), update(), delete().

~~~python
from PyQt6.QtWidgets import *
from db_units.database import Database


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.db = Database()
        self.setWindowTitle("Учёт данных")
        self.resize(800, 500)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.le_name = QLineEdit()
        self.le_name.setPlaceholderText("Название")

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["ID", "Название"])

        self.btn_add = QPushButton("Добавить")
        self.btn_update = QPushButton("Изменить")
        self.btn_delete = QPushButton("Удалить")

        layout.addWidget(self.le_name)
        layout.addWidget(self.table)
        layout.addWidget(self.btn_add)
        layout.addWidget(self.btn_update)
        layout.addWidget(self.btn_delete)

        self.btn_add.clicked.connect(self.add_record)
        self.btn_update.clicked.connect(self.update_record)
        self.btn_delete.clicked.connect(self.delete_record)

        self.load_data()

    def load_data(self):
        rows = self.db.get_all()
        self.table.setRowCount(len(rows))

        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(value)))

    def selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите запись")
            return None
        return int(self.table.item(row, 0).text())

    def add_record(self):
        name = self.le_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название")
            return

        try:
            self.db.add(name)
            self.le_name.clear()
            self.load_data()
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", str(exc))

    def update_record(self):
        record_id = self.selected_id()
        if record_id is None:
            return

        name = self.le_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название")
            return

        try:
            self.db.update(record_id, name)
            self.load_data()
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", str(exc))

    def delete_record(self):
        record_id = self.selected_id()
        if record_id is None:
            return

        try:
            self.db.delete(record_id)
            self.load_data()
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", str(exc))

    def closeEvent(self, event):
        self.db.close()
        super().closeEvent(event)
~~~

Не пытайся выучить весь шаблон посимвольно. Пойми пять методов:
- load_data — получить данные и показать;
- selected_id — узнать ID выбранной записи;
- add_record — добавить;
- update_record — изменить;
- delete_record — удалить.

---

## 13. Шпаргалка по методам PyQt6

### Окно и виджеты

| Код | Значение |
|---|---|
| setWindowTitle("...") | Заголовок окна |
| resize(800, 600) | Размер окна |
| setCentralWidget(widget) | Центральный виджет QMainWindow |
| layout.addWidget(widget) | Добавить виджет |
| layout.addLayout(layout2) | Добавить вложенный layout |
| widget.show() | Показать |
| widget.hide() | Скрыть |
| widget.setEnabled(False) | Заблокировать |
| widget.setEnabled(True) | Разрешить взаимодействие |

### Получение и установка значений

| Виджет | Получить | Установить |
|---|---|---|
| QLineEdit | text() | setText("...") |
| QTextEdit | toPlainText() | setPlainText("...") |
| QSpinBox | value() | setValue(10) |
| QComboBox | currentText() | setCurrentText("...") |
| QCheckBox | isChecked() | setChecked(True) |
| QTableWidget | currentRow() | setItem(row, col, item) |

### Диалоговые сообщения

~~~python
QMessageBox.information(self, "Успех", "Данные сохранены")
QMessageBox.warning(self, "Предупреждение", "Заполните поля")
QMessageBox.critical(self, "Ошибка", "Не удалось выполнить операцию")
~~~

### Полезные сигналы

~~~python
button.clicked.connect(self.method)
combo.currentTextChanged.connect(self.method)
line.textChanged.connect(self.method)
table.itemSelectionChanged.connect(self.method)
~~~

Некоторые сигналы передают аргумент. Например currentTextChanged передаёт новый текст. Если обработчик не принимает аргумент, при необходимости используй lambda.

---

## 14. Типичные ошибки

| Ошибка | Причина | Что проверить |
|---|---|---|
| ModuleNotFoundError: PyQt6 | Библиотека не установлена | pip install PyQt6 |
| ModuleNotFoundError: psycopg2 | Нет драйвера | pip install psycopg2-binary |
| ModuleNotFoundError: dotenv | Нет python-dotenv | pip install python-dotenv |
| connection refused | PostgreSQL не запущен или неверный порт | Службу, host, port |
| database does not exist | База не создана | Имя БД в настройках |
| relation does not exist | Таблица не создана или другое имя | Выполнить schema.sql |
| column does not exist | Неверное имя столбца | Сверить SQL со схемой |
| not all arguments converted | Не совпало число %s и параметров | Проверить плейсхолдеры и кортеж |
| INSERT не сохраняется | Нет commit или запрос упал | commit(), исключение, rollback() |
| Кнопка ничего не делает | Нет connect() | Проверить clicked.connect |
| Метод запускается сразу | Скобки в connect | Передавать self.method без () |
| Таблица не обновляется | Не вызван метод загрузки | load_data() после CRUD |
| NoneType при выборе | Строка не выделена | Проверить currentRow() |
| Изменились все записи | В UPDATE нет WHERE | Добавить WHERE id = %s |
| Удалились все записи | В DELETE нет WHERE | Добавить WHERE id = %s |
| Нет изображения | Неверный путь или файла нет | Проверить путь и QPixmap.isNull() |

### Как искать ошибку

1. Посмотри последнюю строку traceback — там тип ошибки и место.
2. Проверь имена переменных и методов.
3. Проверь, создан ли объект до использования.
4. Проверь количество аргументов метода.
5. Если ошибка SQL — выполни запрос отдельно в pgAdmin.
6. Если кнопка не работает — проверь connect().
7. Если данные не отображаются — отдельно проверь SELECT и вызов обновления UI.

---

## 15. Что важно улучшить в текущем проекте

Проект полезен как учебный пример, но есть нюансы:

1. **Авторизация создаёт новое подключение.** В Auth.show_page1() вызывается QwerSql(), но соединение после запроса явно не закрывается. Лучше передавать уже существующий объект БД или закрывать отдельное соединение.
2. **Пароли хранятся открытым текстом.** Только учебное упрощение. В реальном приложении хранится хэш.
3. **Используется import *.** Для быстрого учебного кода удобно, но в аккуратном проекте лучше импортировать только нужные классы.
4. **UI импортирует класс БД.** Чище, когда главное окно передаёт данные или объект БД в диалог.
5. **Нужна проверка значений до SQL.** Например, пустое название, отрицательная цена, некорректный телефон.
6. **При ошибке запроса нужен rollback().** Иначе соединение может остаться в состоянии неудачной транзакции.
7. **Не публикуй секреты.** Файл .env должен быть в .gitignore; в репозитории оставляют .env.example без реального пароля.

---

## 16. Как готовиться сегодня, если контрольная завтра

Если времени мало, занимайся в таком порядке:

1. **30 минут:** QMainWindow, QWidget, layout, QPushButton, QLineEdit, QTableWidget.
2. **30 минут:** подключение psycopg2 и методы SELECT / INSERT / UPDATE / DELETE.
3. **30 минут:** самостоятельно написать load_data() и заполнение QTableWidget.
4. **30 минут:** связать кнопки с методами через clicked.connect().
5. **20 минут:** получить ID выбранной строки и сделать DELETE.
6. **20 минут:** commit, rollback, QMessageBox и типичные ошибки.

Лучше один раз написать маленький CRUD самостоятельно, чем пять раз перечитать большой проект.

---

## 17. Самопроверка: объясни это преподавателю

Попробуй ответить без подсказки:

1. Для чего нужен QApplication?
2. Почему главное окно наследуется от QMainWindow?
3. Зачем вызывается super().__init__()?
4. Чем QVBoxLayout отличается от QHBoxLayout?
5. Что означает btn.clicked.connect(self.add_record)?
6. Почему в connect не нужны скобки после имени метода?
7. Чем self.name отличается от локальной переменной name?
8. Для чего psycopg2.connect()?
9. Чем курсор отличается от соединения?
10. Чем fetchone() отличается от fetchall()?
11. Зачем commit() после INSERT/UPDATE/DELETE?
12. Для чего rollback()?
13. Почему параметры SQL передаются через %s, а не f-строкой?
14. Как заполнить QTableWidget после SELECT?
15. Почему ID нельзя путать с номером строки?
16. Зачем после добавления вызывать load_data()?
17. Что произойдёт, если забыть WHERE в UPDATE?
18. Как передать данные в другое окно?
19. Как показать ошибку пользователю?
20. Где закрывать соединение с БД?

Если можешь объяснить большую часть, ты понимаешь основу, а не просто копируешь код.

---

## 18. Самая короткая памятка

~~~text
1. Окно:
   class MainWindow(QMainWindow)
   super().__init__()

2. Интерфейс:
   central = QWidget()
   self.setCentralWidget(central)
   layout = QVBoxLayout(central)

3. Кнопка:
   self.btn = QPushButton("Добавить")
   layout.addWidget(self.btn)

4. Связь:
   self.btn.clicked.connect(self.add_record)

5. Получить:
   name = self.le_name.text().strip()

6. Проверить:
   if not name:
       QMessageBox.warning(...)
       return

7. Вызвать БД:
   self.db.add(name)

8. SQL:
   cursor.execute("INSERT ... VALUES (%s)", (name,))
   conn.commit()

9. Обновить:
   self.load_data()

10. Закрыть:
    self.db.close()
~~~

**Главная формула контрольной:**

> **Виджет → сигнал → метод окна → проверка → метод БД → SQL → commit → обновление виджета.**

Если запомнишь эту цепочку, сможешь адаптировать один шаблон под товары, студентов, книги, сотрудников, заявки и почти любую простую систему учёта.
