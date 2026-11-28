# Подготовка к проекту PyQt6 Shop — подробный конспект

> Документ собирает решения и объяснения из нашей работы над учебным настольным приложением-каталогом магазина на Python, PyQt6 и PostgreSQL. Примеры показывают согласованную архитектуру и подходы; они не означают, что весь код уже добавлен и протестирован в проекте.

## 1. Цель проекта

Приложение должно подключаться к PostgreSQL, получать товары, показывать их в виде карточек, поддерживать поиск, фильтрацию и сортировку. В перспективе — добавление товаров, корзина и оформление заказов. Исходные данные отдельно загружаются из Excel.

Главный принцип: **SQL обрабатывает данные, Python связывает слои приложения, PyQt6 отвечает за интерфейс**.

## 2. Архитектура

Рекомендуемая структура (имена папок можно согласовать с уже существующими DB_Units и UI_Windows):

~~~text
PyQt6_Shop_Example/
├── database/
│   └── database_config.py
├── models/
│   └── all_models.py
├── repositories/
│   └── product_repository.py
├── services/
│   └── product_service.py
├── ui_windows/
│   ├── main_window.py
│   └── card.py
├── sql/
│   └── products/
│       ├── get_all_products.sql
│       ├── search_products.sql
│       └── get_filtered_products.sql
├── etl/
│   ├── extract.py
│   ├── transform.py
│   ├── load.py
│   └── main.py
└── main.py
~~~

| Слой | Ответственность |
|---|---|
| database | Подключение и закрытие соединения с PostgreSQL |
| models | Python-представление сущностей |
| repositories | SQL-запросы и взаимодействие с БД |
| services | Бизнес-логика и проверка входных данных |
| ui_windows | Окна, поля ввода, карточки, обработка событий |
| sql | SQL-скрипты отдельно от Python |
| etl | Чтение Excel, преобразование, загрузка |
| main.py | Создание объектов и связывание зависимостей |

Почему разделяем слои: если обработчик кнопки одновременно выполняет SQL, проверяет данные и рисует карточки, код становится трудно тестировать и поддерживать. UI обращается к Service, Service — к Repository, Repository выполняет запрос.

## 3. Подключение к PostgreSQL через psycopg2

Мы решили продолжать использовать **psycopg2**, без перехода на SQLAlchemy.

~~~python
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


class DBConn:
    def __init__(self):
        try:
            self.conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                database=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                port=os.getenv("DB_PORT"),
                client_encoding="UTF-8",
            )
        except psycopg2.Error as error:
            print(f"Ошибка подключения: {error}")
            raise

    def close(self):
        if self.conn is not None and not self.conn.closed:
            self.conn.close()
~~~

Пример .env:

~~~dotenv
DB_HOST=localhost
DB_NAME=shop_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_PORT=5432
~~~

- load_dotenv() загружает переменные из .env.
- os.getenv() читает значение переменной окружения.
- psycopg2.connect() открывает соединение.
- self.conn хранит соединение, через которое репозитории создают курсоры.
- close() закрывает соединение.

Не публикуй настоящий .env в GitHub. Храни .env.example с названиями переменных и демонстрационными значениями. Для учебной версии можно создать соединение при запуске и передать объект репозиториям. В более крупном приложении используют пул соединений и более строгий контроль жизненного цикла.

## 4. Схема PostgreSQL

Обсуждали шесть таблиц:

### categories
- id — первичный ключ;
- name — уникальное название категории;
- description — описание.

### products
- id — первичный ключ;
- name — название товара;
- description — описание;
- price — NUMERIC(10,2), цена неотрицательная;
- stock — остаток, неотрицательный;
- category_id — внешний ключ на categories.id.

### customers
- id — первичный ключ;
- full_name — имя покупателя;
- email — email, может быть уникальным;
- phone — телефон.

### suppliers
- id — первичный ключ;
- name — название поставщика;
- email, phone — контакты.

### orders
- id — первичный ключ;
- customer_id — внешний ключ на customers.id;
- order_date — дата заказа;
- status — статус;
- total_amount — неотрицательная сумма заказа.

### order_items
- id — первичный ключ;
- order_id — внешний ключ на orders.id;
- product_id — внешний ключ на products.id;
- quantity — количество строго больше нуля;
- unit_price — цена на момент покупки;
- UNIQUE(order_id, product_id) — товар не дублируется в рамках одного заказа.

Связи:
- одна категория содержит много товаров;
- один покупатель может иметь много заказов;
- один заказ содержит несколько позиций;
- один товар может присутствовать во многих заказах;
- связь orders и products реализована через order_items.

Почему unit_price хранится в order_items: цена в каталоге может измениться. В заказе должна сохраниться историческая цена, по которой покупатель приобрёл товар.

Индексы обсуждались на products(category_id), products(name), orders(customer_id), order_items(order_id). Индекс ускоряет подходящие запросы, но занимает место и увеличивает стоимость INSERT/UPDATE/DELETE. Индексы выбирают исходя из запросов, а не создают на каждом поле автоматически.

## 5. Модели Python и dataclass

Модель описывает представление строки БД в Python. **@dataclass не создаёт таблицу PostgreSQL** — таблицы создаются SQL-командами CREATE TABLE.

~~~python
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class Category:
    id: int
    name: str
    description: str | None = None


@dataclass
class Product:
    id: int
    name: str
    description: str | None
    price: Decimal
    stock: int
    category_id: int


@dataclass
class Customer:
    id: int
    full_name: str
    email: str | None = None
    phone: str | None = None


@dataclass
class Supplier:
    id: int
    name: str
    email: str | None = None
    phone: str | None = None


@dataclass
class Order:
    id: int
    customer_id: int
    order_date: datetime
    status: str
    total_amount: Decimal


@dataclass
class OrderItem:
    id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price: Decimal
~~~

Декоратор @dataclass автоматически генерирует стандартные методы, включая __init__. После этого можно создать объект и обращаться к его полям:

~~~python
from decimal import Decimal

product = Product(
    id=1,
    name="RTX 4070",
    description="Видеокарта",
    price=Decimal("59999.00"),
    stock=5,
    category_id=1,
)

print(product.name)
print(product.price)
~~~

Почему Decimal: PostgreSQL NUMERIC предназначен для точных десятичных значений. Для денег в Python лучше Decimal, а не float, поскольку float может давать погрешности.

Запись str | None означает, что поле может содержать строку или None. Если модель используется для создания новой записи до получения ID, поле id можно сделать необязательным. В dataclass обязательные поля должны идти раньше полей со значениями по умолчанию:

~~~python
@dataclass
class Product:
    name: str
    description: str | None
    price: Decimal
    stock: int
    category_id: int
    id: int | None = None
~~~

## 6. Repository и выполнение SQL

Repository отвечает за SQL и доступ к данным. Он не должен знать о PyQt.

~~~python
from psycopg2.extras import RealDictCursor
from models.all_models import Product


class ProductRepository:
    def __init__(self, database):
        self.database = database

    def get_all(self):
        with self.database.conn.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:
            cursor.execute("""
                SELECT id, name, description, price, stock, category_id
                FROM products
                ORDER BY id;
            """)
            rows = cursor.fetchall()

        return [Product(**dict(row)) for row in rows]
~~~

Курсор — объект, через который выполняется SQL и читаются результаты:
- execute(sql) — выполнить запрос;
- fetchall() — получить все строки;
- fetchone() — получить одну строку;
- контекстный менеджер with закрывает курсор после блока.

RealDictCursor возвращает строки, к полям которых можно обращаться по названиям столбцов. Поэтому можно преобразовать строку в dict и создать Product через Product(**dict(row)). Это сработает, если имена выбранных столбцов совпадают с полями dataclass и выбраны все обязательные поля.

## 7. Хранение SQL в отдельных файлах

Поскольку ты обычно пишешь запросы SQL-скриптами, можно хранить их отдельно от Python:

~~~text
sql/
└── products/
    ├── get_all_products.sql
    ├── search_products.sql
    └── get_filtered_products.sql
~~~

Пример get_all_products.sql:

~~~sql
SELECT
    id,
    name,
    description,
    price,
    stock,
    category_id
FROM products
ORDER BY id;
~~~

Repository читает файл и передаёт его psycopg2:

~~~python
from pathlib import Path
from psycopg2.extras import RealDictCursor
from models.all_models import Product


class ProductRepository:
    def __init__(self, database):
        self.database = database
        self.sql_dir = (
            Path(__file__).resolve().parent.parent
            / "sql"
            / "products"
        )

    def _read_query(self, filename):
        path = self.sql_dir / filename
        return path.read_text(encoding="utf-8")

    def get_all(self):
        sql = self._read_query("get_all_products.sql")

        with self.database.conn.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()

        return [Product(**dict(row)) for row in rows]
~~~

Python здесь не заменяет SQL-логику: он читает файл, передаёт параметры и получает результат.

## 8. Параметры SQL и безопасность

Для значений, пришедших от пользователя, применяй плейсхолдеры psycopg2:

~~~python
cursor.execute(
    "SELECT * FROM products WHERE id = %s",
    (product_id,)
)
~~~

Запятая в (product_id,) важна: это кортеж из одного элемента.

Не собирай SQL через f-string с пользовательским вводом: это создаёт риск SQL-инъекции и проблем с кавычками. Имена столбцов и направление сортировки нельзя передавать как обычные параметры %s. Для динамического ORDER BY используется заранее определённый allowlist — белый список безопасных SQL-фрагментов.

## 9. Service — бизнес-логика

Service связывает UI и Repository. Он не должен содержать Qt-код или самостоятельно создавать SQL.

~~~python
class ProductService:
    def __init__(self, product_repository):
        self.product_repository = product_repository

    def get_all_products(self):
        return self.product_repository.get_all()

    def search_products(self, query):
        query = query.strip()

        if not query:
            return self.get_all_products()

        return self.product_repository.search(query)
~~~

Дальше в Service можно проверять диапазон цен, корректность категории и правила изменения товара.

Поток вызова: UI получает ввод → Service проверяет данные → Repository выполняет SQL → Service возвращает результат → UI отображает результат.

## 10. MainWindow, QScrollArea и карточки

Для длинного каталога нужен QScrollArea. Важно: **QScrollArea прокручивает виджет, переданный в setWidget(), а не сам QGridLayout**. Поэтому создаём отдельный QWidget-контейнер, помещаем в него QGridLayout, а контейнер устанавливаем в ScrollArea.

~~~python
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QScrollArea,
    QGridLayout,
)

from ui_windows.card import ProductCard


class MainWindow(QMainWindow):
    def __init__(self, product_service):
        super().__init__()

        self.product_service = product_service
        self.setWindowTitle("Product Catalog")
        self.resize(1000, 700)

        self.init_ui()
        self.load_products()

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        # Контейнер для содержимого каталога
        self.products_widget = QWidget()

        # Сетка, в которой будут карточки
        self.products_layout = QGridLayout(self.products_widget)

        # ScrollArea прокручивает products_widget
        self.scroll_area.setWidget(self.products_widget)

        self.main_layout.addWidget(self.scroll_area)
~~~

Разница между объектами:
- QWidget — визуальный виджет-контейнер;
- QGridLayout — менеджер размещения виджетов по строкам и столбцам;
- QVBoxLayout — вертикально располагает элементы;
- QScrollArea — даёт прокрутку дочернего виджета.

### Карточка ProductCard

Удобнее передавать в карточку целый объект Product, а не набор отдельных значений:

~~~python
class ProductCard(QFrame):
    def __init__(self, product, parent=None):
        super().__init__(parent)
        self.product = product
        self.init_ui()
~~~

Внутри карточки используем self.product.name, self.product.price, self.product.stock и self.product.description. Если понадобится изображение, нужно отдельно добавить поле пути/URL или механизм получения изображения: в текущей модели поля изображения нет.

### Загрузка и отображение

~~~python
def load_products(self):
    products = self.product_service.get_all_products()
    self.display_products(products)


def display_products(self, products):
    self.clear_layout()

    for index, product in enumerate(products):
        card = ProductCard(product)

        row = index // 3
        column = index % 3

        self.products_layout.addWidget(card, row, column)
~~~

Число 3 означает, что в строке будет три карточки. Для каждого индекса:
- index // 3 вычисляет номер строки;
- index % 3 вычисляет номер столбца.

| index | row | column |
|---:|---:|---:|
| 0 | 0 | 0 |
| 1 | 0 | 1 |
| 2 | 0 | 2 |
| 3 | 1 | 0 |
| 4 | 1 | 1 |
| 5 | 1 | 2 |

## 11. Как очищать Layout

При поиске или фильтрации старые карточки не должны оставаться в Layout. Поэтому до добавления новых карточек очищаем прежние:

~~~python
def clear_layout(self):
    while self.products_layout.count():
        item = self.products_layout.takeAt(0)

        widget = item.widget()

        if widget is not None:
            widget.deleteLater()
~~~

Разбор:
1. count() возвращает число элементов в Layout.
2. takeAt(0) извлекает первый элемент и удаляет его из структуры размещения.
3. item.widget() возвращает виджет, если элемент содержит виджет.
4. deleteLater() просит Qt удалить объект после обработки текущих событий.

Почему while: число элементов уменьшается после каждого takeAt(0), и цикл работает, пока Layout не станет пустым.

Этот простой метод рассчитан на Layout, в котором лежат карточки-виджеты. Если позже появятся вложенные Layout или spacer-элементы, их нужно обрабатывать отдельно, при необходимости рекурсивно.

Полный цикл обновления:
1. Получить новые товары через Service.
2. Вызвать display_products(products).
3. Очистить старые карточки через clear_layout().
4. Создать новые ProductCard.
5. Добавить карточки в QGridLayout.

**ScrollArea и Layout создаются один раз в init_ui(). При поиске не создаём новый ScrollArea — меняем только содержимое products_layout.**

## 12. Поиск, фильтрация и сортировка через SQL

Мы выбрали подход, при котором PostgreSQL выполняет поиск и фильтрацию. Не нужно каждый раз загружать все товары в Python и фильтровать их в памяти.

### Поиск по названию

PostgreSQL ILIKE выполняет поиск без учёта регистра:

~~~sql
SELECT id, name, description, price, stock, category_id
FROM products
WHERE name ILIKE %s
ORDER BY id;
~~~

Repository передаёт шаблон:

~~~python
cursor.execute(sql, (f"%{query}%",))
~~~

Если query = RTX, шаблон будет %RTX% — найдутся названия, в которых RTX встречается в любой позиции.

### Фильтр по категории

~~~sql
SELECT id, name, description, price, stock, category_id
FROM products
WHERE category_id = %s
ORDER BY id;
~~~

### Диапазон цены

~~~sql
SELECT id, name, description, price, stock, category_id
FROM products
WHERE price BETWEEN %s AND %s
ORDER BY price;
~~~

BETWEEN включает обе границы диапазона.

### Только товары в наличии

~~~sql
SELECT id, name, description, price, stock, category_id
FROM products
WHERE stock > 0
ORDER BY id;
~~~

### Сортировка

~~~sql
-- Сначала дешёвые
ORDER BY price ASC;

-- Сначала дорогие
ORDER BY price DESC;

-- По названию
ORDER BY name ASC;

-- По остатку
ORDER BY stock DESC;
~~~

ASC — по возрастанию, DESC — по убыванию.

### Безопасный allowlist для сортировки

~~~python
SORT_OPTIONS = {
    "По умолчанию": "id ASC",
    "Сначала дешёвые": "price ASC",
    "Сначала дорогие": "price DESC",
    "По названию": "name ASC",
    "По остатку": "stock DESC",
}
~~~

Repository должен выбирать фрагмент сортировки только из этого словаря. Значения поиска, категории и цены всё равно передаются через %s. Не вставляй пользовательский текст напрямую в ORDER BY.

### Объединение фильтров

Можно использовать один общий запрос и добавлять только нужные условия:

~~~python
conditions = []
params = []

if query:
    conditions.append("name ILIKE %s")
    params.append(f"%{query}%")

if category_id is not None:
    conditions.append("category_id = %s")
    params.append(category_id)

if min_price is not None:
    conditions.append("price >= %s")
    params.append(min_price)

if max_price is not None:
    conditions.append("price <= %s")
    params.append(max_price)

if only_available:
    conditions.append("stock > 0")

sql = """
    SELECT id, name, description, price, stock, category_id
    FROM products
"""

if conditions:
    sql += " WHERE " + " AND ".join(conditions)

sql += " ORDER BY " + SORT_OPTIONS[sort_label]
~~~

После этого Repository выполняет cursor.execute(sql, tuple(params)) и получает строки. В SQL добавляются только условия, написанные разработчиком, и проверенный фрагмент сортировки из allowlist. Пользовательские значения остаются параметрами.

## 13. События PyQt6 и живой поиск

Для поля поиска подходит сигнал textChanged:

~~~python
self.search_input.textChanged.connect(self.on_search_changed)
~~~

Обработчик может получить результаты через Service и обновить карточки:

~~~python
def on_search_changed(self, text):
    products = self.product_service.search_products(text)
    self.display_products(products)
~~~

Но поиск на каждый символ может создавать слишком много запросов.

### Debounce через QTimer

Чтобы подождать около 300 мс после последнего символа:

~~~python
from PyQt6.QtCore import QTimer

self.search_timer = QTimer(self)
self.search_timer.setSingleShot(True)
self.search_timer.setInterval(300)
self.search_timer.timeout.connect(self.perform_search)

self.search_input.textChanged.connect(
    lambda: self.search_timer.start()
)


def perform_search(self):
    query = self.search_input.text()
    products = self.product_service.search_products(query)
    self.display_products(products)
~~~

Логика:
1. Пользователь вводит символ.
2. Таймер запускается на 300 мс.
3. Если до истечения времени введён следующий символ, таймер перезапускается.
4. После паузы вызывается perform_search().
5. Выполняется один запрос и обновляется каталог.

Для большого каталога или тяжёлых запросов стоит выполнять обращение к БД в отдельном потоке, чтобы не блокировать GUI-поток. Для первой небольшой версии можно начать с простого синхронного варианта.

## 14. ETL: Pandas, Excel и PostgreSQL

Отдельно обсуждали задачу: прочитать три Excel-файла, преобразовать данные в несколько таблиц (ориентир — 7–8) и загрузить в PostgreSQL.

ETL состоит из трёх этапов:
- Extract — чтение источников;
- Transform — очистка и преобразование;
- Load — загрузка в БД.

### Чтение Excel

~~~python
import pandas as pd

df = pd.read_excel("source.xlsx", sheet_name="Лист1")
~~~

Чтобы прочитать все листы:

~~~python
sheets = pd.read_excel("source.xlsx", sheet_name=None)
~~~

В этом случае Pandas вернёт словарь DataFrame по листам.

### Очистка и преобразование

В зависимости от файлов могут потребоваться:
- rename() — переименование столбцов;
- dropna(how="all") — удаление полностью пустых строк;
- astype() — изменение типов;
- to_datetime() — преобразование дат;
- str.strip() — удаление пробелов по краям строк;
- drop_duplicates() — удаление дубликатов;
- проверка обязательных полей;
- разделение исходного DataFrame на несколько DataFrame для разных таблиц.

Не удаляй дубликаты без бизнес-правила уникальности. Две строки с одинаковым названием товара могут быть разными товарами, если у них разные артикулы.

### Загрузка через psycopg2

Если используется только psycopg2, DataFrame.to_sql() напрямую не подходит: этот метод обычно использует SQLAlchemy Engine. Для текущего стека подойдут psycopg2.extras.execute_values или executemany.

~~~python
from psycopg2.extras import execute_values


def insert_products(conn, rows):
    sql = """
        INSERT INTO products
            (name, description, price, stock, category_id)
        VALUES %s
    """

    with conn.cursor() as cursor:
        execute_values(cursor, sql, rows)

    conn.commit()
~~~

Строки rows должны иметь значения в том же порядке, что и столбцы INSERT. Денежные значения лучше передавать как Decimal.

### Порядок загрузки

Сначала родительские таблицы, затем дочерние, чтобы внешние ключи ссылались на существующие записи. Возможный порядок для обсуждавшейся схемы:
1. categories;
2. products;
3. customers;
4. suppliers;
5. orders;
6. order_items.

Точный порядок зависит от внешних ключей.

### Транзакции

~~~python
try:
    # INSERT / UPDATE нескольких таблиц
    conn.commit()
except Exception:
    conn.rollback()
    raise
~~~

commit() подтверждает изменения. rollback() отменяет незакоммиченные изменения при ошибке. Для загрузки полезно логировать количество прочитанных, обработанных, загруженных и отклонённых строк.

## 15. Связывание зависимостей в main.py

Главный файл создаёт компоненты и передаёт зависимости:

~~~python
import sys
from PyQt6.QtWidgets import QApplication

from database.database_config import DBConn
from repositories.product_repository import ProductRepository
from services.product_service import ProductService
from ui_windows.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    database = DBConn()
    product_repository = ProductRepository(database)
    product_service = ProductService(product_repository)

    window = MainWindow(product_service)
    window.show()

    exit_code = app.exec()
    database.close()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
~~~

Это называется связыванием зависимостей: Repository получает подключение, Service получает Repository, MainWindow получает Service. В более надёжной версии закрытие соединения стоит гарантировать через try/finally, чтобы оно закрылось и при исключении.

## 16. Частые ошибки и различия

- **Dataclass — не таблица БД.** Dataclass описывает объект Python; таблица создаётся SQL DDL.
- **SQL не должен находиться в MainWindow.** UI вызывает Service, а Repository выполняет SQL.
- **Не создавай ScrollArea при каждом поиске.** Она создаётся один раз; при обновлении очищается и наполняется Layout карточек.
- **Не забывай очищать Layout.** Иначе старые карточки останутся.
- **Не подставляй пользовательские значения в SQL через f-string.** Используй параметры %s.
- **Не подставляй произвольный ORDER BY.** Используй allowlist.
- **Для денег используй Decimal и NUMERIC.**
- **Загружай родительские записи до дочерних.** Иначе нарушатся внешние ключи.
- **ScrollArea прокручивает QWidget, а не Layout.** Передавай контейнер через setWidget().
- **Не фильтруй огромный набор данных в интерфейсе без необходимости.** Поиск и сортировку каталога выполняет PostgreSQL.

## 17. Рекомендуемый порядок разработки и проверки

1. Проверить подключение к PostgreSQL отдельным коротким скриптом.
2. Убедиться, что products содержит тестовые записи.
3. Создать и проверить dataclass Product.
4. Реализовать ProductRepository.get_all() и проверить результат в консоли.
5. Реализовать ProductService.get_all_products().
6. Создать ProductCard, принимающую объект Product.
7. Создать MainWindow и ScrollArea.
8. Проверить отображение нескольких тестовых карточек.
9. Подключить реальные данные через Service.
10. Реализовать clear_layout() и повторное отображение.
11. Добавить поиск через ILIKE.
12. Добавить фильтр по категории, цене и наличию.
13. Добавить сортировку через allowlist.
14. Добавить debounce для живого поиска.
15. Отдельно реализовать ETL и проверить на небольшом наборе строк.
16. Проверить пустые результаты, ошибки и закрытие соединения.

## 18. Контрольные вопросы для подготовки

Попробуй ответить на вопросы самостоятельно:
1. Чем QWidget отличается от QLayout?
2. Почему QScrollArea получает QWidget через setWidget()?
3. Для чего нужен QGridLayout?
4. Что делает takeAt(0)?
5. Зачем нужен deleteLater()?
6. Почему Layout очищают перед повторным отображением карточек?
7. Что такое сигнал textChanged?
8. Для чего нужен debounce и почему выбран интервал около 300 мс?
9. Чем Repository отличается от Service?
10. Почему MainWindow не должен выполнять SQL?
11. Что делает RealDictCursor?
12. При каких условиях Product(**dict(row)) сработает?
13. Чем ILIKE отличается от LIKE в PostgreSQL?
14. Что означают ASC и DESC?
15. Почему нельзя без проверки подставлять ORDER BY от пользователя?
16. Как psycopg2 передаёт параметры запроса?
17. Почему для денег лучше Decimal?
18. Что такое ETL и чем отличаются Extract, Transform и Load?
19. Почему родительские таблицы загружают раньше дочерних?
20. Для чего нужны commit() и rollback()?

## 19. Краткая шпаргалка

| Задача | Инструмент |
|---|---|
| Подключение к PostgreSQL | psycopg2.connect |
| Создать курсор | conn.cursor() |
| Выполнить SQL | cursor.execute() |
| Передать параметры | %s и tuple |
| Получить все строки | fetchall() |
| Получить одну строку | fetchone() |
| Словарные строки | RealDictCursor |
| Описать объект | @dataclass |
| Денежные значения | Decimal |
| Контейнер окна | QWidget |
| Вертикальное размещение | QVBoxLayout |
| Сетка карточек | QGridLayout |
| Прокрутка | QScrollArea |
| Установить прокручиваемый виджет | setWidget() |
| Подстройка размера содержимого | setWidgetResizable(True) |
| Число элементов Layout | count() |
| Извлечь элемент Layout | takeAt() |
| Отложенное удаление Qt-объекта | deleteLater() |
| Сигнал изменения текста | textChanged |
| Debounce-таймер | QTimer |
| Поиск без учёта регистра | ILIKE |
| Сортировка | ORDER BY |
| Чтение Excel | pandas.read_excel |
| Массовая вставка | execute_values |
| Подтвердить транзакцию | commit() |
| Откатить транзакцию | rollback() |

---

**Главный принцип проекта:** интерфейс отображает данные и собирает ввод; Service управляет логикой; Repository исполняет SQL; PostgreSQL хранит и обрабатывает данные. ETL — отдельный процесс подготовки и загрузки данных.
