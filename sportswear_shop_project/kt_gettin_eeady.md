# PyQt6: карточки товаров, изображения и PostgreSQL

Практическая шпаргалка для контрольной по PyQt6 на примере магазина спортивной одежды.

Цель — научиться самостоятельно:
- получать список товаров из PostgreSQL;
- превращать строки из БД в карточки;
- показывать локальные изображения из папки \`resources\`;
- размещать карточки в окне через Layout;
- открывать подробную информацию о товаре по клику;
- обновлять каталог и очищать старые карточки;
- понимать, где должны находиться SQL, интерфейс и логика.

Материал специально построен вокруг простой архитектуры: \`db_units/config.py\`, \`product_card.py\`, \`ui_window.py\`. Это близко к подходу, когда подключение и функции БД находятся отдельно, а PyQt6-разметка и управление окном — в UI.

---

# 1. Самая простая архитектура

Для небольшой учебной программы не нужно сразу вводить MVC, Repository, Service, DI и множество дополнительных папок. Достаточно разделить ответственность между тремя файлами.

Рекомендуемая структура:

\`\`\`text
sportswear_shop_project/
│
├── main.py
├── ui_window.py
├── product_card.py
│
├── db_units/
│   ├── __init__.py
│   └── config.py
│
├── resources/
│   ├── hoodie.jpg
│   ├── leggings.jpg
│   ├── shorts.jpg
│   └── ...
│
├── .env
└── requirements.txt
\`\`\`

## За что отвечает каждый файл

| Файл | Ответственность |
|---|---|
| \`db_units/config.py\` | Подключение к PostgreSQL, SELECT, INSERT, UPDATE, DELETE |
| \`product_card.py\` | Внешний вид одной карточки и реакция на клик по ней |
| \`ui_window.py\` | Главное окно, Layout, получение товаров из БД, создание карточек |
| \`main.py\` | Запуск приложения |

**Главное правило:** SQL-запросы не нужно писать внутри метода, который создаёт QLabel или QPushButton. А класс карточки не должен самостоятельно подключаться к PostgreSQL. Главное окно получает данные через модуль БД и передаёт их карточкам.

Для совсем маленькой контрольной можно временно держать класс карточки в \`ui_window.py\`. Но если карточек и экранов несколько, отдельный \`product_card.py\` понятнее.

---

# 2. Как данные проходят от PostgreSQL до экрана

Представим, что в таблице или представлении \`v_products_full\` лежат товары.

\`\`\`text
PostgreSQL
    |
    | SELECT товаров
    v
db_units/config.py
    |
    | возвращает список строк
    v
ui_window.py
    |
    | перебирает товары в цикле
    | для каждого товара создаёт ProductCard(product)
    v
product_card.py
    |
    | показывает название, цену, фото
    v
Пользователь видит каталог
\`\`\`

Например, БД вернула три товара:

\`\`\`python
[
    (1, "Худи", 4500, "resources/hoodie.jpg"),
    (2, "Леггинсы", 3200, "resources/leggings.jpg"),
    (3, "Шорты", 1800, "resources/shorts.jpg")
]
\`\`\`

Это список, в котором каждый элемент — отдельный товар. В данном примере товар представлен кортежем (tuple).

- \`product[0]\` — ID;
- \`product[1]\` — название;
- \`product[2]\` — цена;
- \`product[3]\` — путь к изображению.

Именно такой результат часто возвращает \`cursor.fetchall()\`.

---

# 3. Подключение к PostgreSQL: db_units/config.py

## 3.1. Установка библиотек

Для PostgreSQL в этом примере используется psycopg2:

\`\`\`bash
pip install psycopg2-binary python-dotenv
\`\`\`

## 3.2. Настройки подключения

В корне проекта создаём файл \`.env\`:

\`\`\`env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sportswear_shop
DB_USER=postgres
DB_PASSWORD=your_password
\`\`\`

Не публикуй настоящий пароль в GitHub. Добавь \`.env\` в \`.gitignore\`, а в репозитории оставь только пример настроек без секретов.

## 3.3. Простой класс для работы с БД

Файл \`db_units/config.py\`:

\`\`\`python
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "sportswear_shop"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "")
        )

    def get_products(self):
        """Получить список товаров для каталога."""
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, name, price, image_path
                FROM products
                ORDER BY id
            """)
            return cursor.fetchall()

    def get_product_by_id(self, product_id):
        """Получить один товар по ID."""
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, name, price, image_path, description
                FROM products
                WHERE id = %s
            """, (product_id,))
            return cursor.fetchone()

    def close(self):
        self.conn.close()
\`\`\`

Названия таблицы и колонок в запросе должны соответствовать твоей реальной схеме. В текущем проекте каталог читается из представления \`v_products_full\`, а метод \`show_products()\` возвращает больше полей: категорию, тип, бренд, материал, размер, цвет, количество, цену, скидку и \`image_path\`. Поэтому запрос выше — минимальный учебный пример, а не обязательная замена текущего запроса.

## 3.4. Что здесь важно понимать

\`psycopg2.connect(...)\` открывает соединение с PostgreSQL.

\`self.conn\` — атрибут объекта, в котором хранится соединение. Благодаря \`self\` другие методы класса могут использовать его.

\`cursor()\` создаёт курсор — объект, через который выполняются SQL-запросы.

\`execute()\` отправляет SQL-запрос в БД.

\`fetchall()\` забирает все строки результата и возвращает список кортежей.

\`fetchone()\` забирает только одну строку или возвращает \`None\`, если строка не найдена.

\`close()\` закрывает соединение. Его нужно вызвать при завершении приложения.

### Почему параметры SQL записываются через %s

Правильно:

\`\`\`python
cursor.execute(
    "SELECT * FROM products WHERE id = %s",
    (product_id,)
)
\`\`\`

Не нужно вставлять пользовательское значение в SQL через f-строку. Параметры передаются отдельно — это безопаснее и помогает избежать SQL-инъекций.

Обрати внимание на запятую в \`(product_id,)\`: это кортеж из одного элемента.

## 3.5. Если хочется оставить функции, а не класс

Можно сделать и в привычном процедурном стиле:

\`\`\`python
def get_connection():
    return psycopg2.connect(...)

def get_products():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, price FROM products")
            return cursor.fetchall()
    finally:
        conn.close()
\`\`\`

Но если приложение постоянно работает с БД, удобнее один раз создать объект \`Database\` и вызывать его методы. Важно не открывать новое соединение на каждый товар внутри цикла.

---

# 4. Изображения товаров: как хранить и показывать

Для учебного магазина проще всего хранить сами изображения в папке проекта, а в БД — только путь к файлу.

Например:

\`\`\`text
resources/
├── hoodie.jpg
├── leggings.jpg
├── shorts.jpg
└── tshirt.jpg
\`\`\`

В таблице:

| id | name | image_path |
|---:|---|---|
| 1 | Худи | resources/hoodie.jpg |
| 2 | Леггинсы | resources/leggings.jpg |
| 3 | Шорты | resources/shorts.jpg |

**Необязательно сохранять картинку в PostgreSQL как BYTEA.** Для небольшого локального приложения обычно проще держать файлы в \`resources\`, а в БД — относительный путь к ним.

## 4.1. QPixmap — загрузка изображения

Для отображения изображения в PyQt6 используется \`QPixmap\`.

\`\`\`python
from PyQt6.QtGui import QPixmap

pixmap = QPixmap("resources/hoodie.jpg")
label.setPixmap(pixmap)
\`\`\`

- \`QPixmap(path)\` загружает картинку с диска;
- \`setPixmap()\` устанавливает её в QLabel.

## 4.2. Масштабирование изображения

Часто исходное фото большое. Его нужно уменьшить под размер карточки:

\`\`\`python
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

pixmap = QPixmap("resources/hoodie.jpg")

label.setPixmap(
    pixmap.scaled(
        180,
        150,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation
    )
)
\`\`\`

Что означают параметры:

- \`180, 150\` — максимальная ширина и высота;
- \`KeepAspectRatio\` — сохранить исходные пропорции, не растягивать фото;
- \`SmoothTransformation\` — сглаживать изображение при изменении размера.

## 4.3. Проверка, что изображение загрузилось

Если путь неправильный, \`QPixmap\` будет пустым. Проверяй это:

\`\`\`python
pixmap = QPixmap(image_path)

if not pixmap.isNull():
    label.setPixmap(
        pixmap.scaled(
            180, 150,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
    )
else:
    label.setText("Нет изображения")
\`\`\`

## 4.4. Почему относительный путь иногда не работает

Путь \`resources/hoodie.jpg\` обычно считается относительно текущей рабочей папки запуска, а не обязательно относительно файла Python.

Чтобы путь не зависел от того, откуда запустили программу, можно вычислить абсолютный путь:

\`\`\`python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
image_path = BASE_DIR / "resources" / "hoodie.jpg"

pixmap = QPixmap(str(image_path))
\`\`\`

Если код находится в подпапке, например \`ui_units\`, нужно подняться на нужное количество уровней через \`.parent\`.

В текущем проекте \`NextWin\` и \`MyWin\` уже используют \`BASE_DIR\` и \`os.path.join()\`. Смысл тот же: получить надёжный путь к файлу.

---

# 5. Создание одной карточки товара: product_card.py

Карточка — это отдельный виджет. Внутри неё могут быть:
- фотография;
- название;
- категория;
- цена;
- кнопка «Подробнее» или «В корзину».

Создадим класс:

\`\`\`python
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, pyqtSignal


class ProductCard(QWidget):
    # Сигнал передаст наружу данные товара при нажатии на кнопку.
    clicked = pyqtSignal(object)

    def __init__(self, product):
        super().__init__()

        # Сохраняем товар внутри конкретной карточки.
        self.product = product

        layout = QVBoxLayout(self)

        # 1. Изображение.
        self.image_label = QLabel()
        self.image_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.image_label.setFixedSize(190, 150)

        image_path = Path(product["image_path"])
        pixmap = QPixmap(str(image_path))

        if not pixmap.isNull():
            self.image_label.setPixmap(
                pixmap.scaled(
                    180, 140,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
        else:
            self.image_label.setText("Нет изображения")

        # 2. Название.
        self.name_label = QLabel(product["name"])
        self.name_label.setWordWrap(True)

        # 3. Цена.
        self.price_label = QLabel(f'{product["price"]} ₽')

        # 4. Кнопка.
        self.button = QPushButton("Подробнее")
        self.button.clicked.connect(self.on_click)

        # Добавляем элементы в карточку.
        layout.addWidget(self.image_label)
        layout.addWidget(self.name_label)
        layout.addWidget(self.price_label)
        layout.addWidget(self.button)

        self.setStyleSheet("""
            ProductCard {
                border: 1px solid #cccccc;
                border-radius: 10px;
                padding: 8px;
            }
            QPushButton {
                padding: 7px;
            }
        """)

    def on_click(self):
        # Отправляем данные товара главному окну.
        self.clicked.emit(self.product)
\`\`\`

Важный момент: здесь товар — словарь. Поэтому поля читаются по ключам:

\`\`\`python
product["name"]
product["price"]
product["image_path"]
\`\`\`

Если из БД приходит кортеж, можно обращаться по индексам: \`product[1]\`, \`product[2]\` и т. д. Но для большого количества полей словарь обычно понятнее.

## 5.1. Что означает self.product = product

Допустим, главное окно создаёт карточку:

\`\`\`python
card = ProductCard(product)
\`\`\`

В конструктор \`__init__\` передаётся конкретный товар. Внутри:

- \`product\` — обычный параметр конструктора;
- \`self.product\` — атрибут конкретного объекта карточки;
- \`self.product = product\` — сохраняем переданный товар внутри объекта.

Зачем это нужно? Чтобы через несколько секунд, когда пользователь нажмёт кнопку, метод \`on_click()\` знал, какой именно товар находится в карточке.

У каждой карточки свои данные:

\`\`\`python
card1 = ProductCard(product_1)
card2 = ProductCard(product_2)

# Внутри card1 хранится product_1.
# Внутри card2 хранится product_2.
\`\`\`

\`self\` — это ссылка на текущий объект. Снаружи обращаются к \`card1.product\`, а не к \`card1.self.product\`.

## 5.2. Почему используется сигнал pyqtSignal

Карточка не должна сама управлять всем главным окном. Она сообщает: «Пользователь выбрал вот этот товар».

\`\`\`python
clicked = pyqtSignal(object)
\`\`\`

Создаёт собственный сигнал, который может передавать объект.

\`\`\`python
self.clicked.emit(self.product)
\`\`\`

Отправляет сохранённый товар.

В главном окне сигнал подключается к обработчику:

\`\`\`python
card.clicked.connect(self.open_product)
\`\`\`

Это позволяет отделить карточку от логики главного окна.

---

# 6. Главное окно: получение товаров и динамическое создание карточек

Теперь соберём каталог в \`ui_window.py\`.

\`\`\`python
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QLabel,
    QVBoxLayout, QGridLayout, QScrollArea
)

from db_units.config import Database
from product_card import ProductCard


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SPORTWEAR")
        self.resize(900, 650)

        # Создаём объект для работы с БД.
        self.db = Database()

        # Центральный виджет главного окна.
        central = QWidget()
        self.setCentralWidget(central)

        # Основной layout.
        main_layout = QVBoxLayout(central)

        title = QLabel("Каталог товаров")
        main_layout.addWidget(title)

        # Создаём контейнер, внутри которого будут карточки.
        self.cards_container = QWidget()

        # Сетка для карточек.
        self.cards_layout = QGridLayout(self.cards_container)

        # Оборачиваем контейнер в прокручиваемую область.
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.cards_container)

        main_layout.addWidget(self.scroll)

        # Загружаем товары при открытии окна.
        self.load_products()

    def load_products(self):
        # Получаем список товаров из БД.
        rows = self.db.get_products()

        # Создаём карточки по одной.
        for index, row in enumerate(rows):
            product = {
                "id": row[0],
                "name": row[1],
                "price": row[2],
                "image_path": row[3]
            }

            card = ProductCard(product)

            # Подключаем клик карточки.
            card.clicked.connect(self.open_product)

            # Рассчитываем позицию в сетке.
            columns = 3
            row_number = index // columns
            column_number = index % columns

            self.cards_layout.addWidget(
                card,
                row_number,
                column_number
            )

    def open_product(self, product):
        print("Выбран товар:", product["name"])
\`\`\`

Здесь показан базовый принцип. Для полноценного окна \`open_product()\` можно заменить на открытие отдельного диалога с подробной информацией.

## 6.1. Самое важное — цикл

\`\`\`python
for index, row in enumerate(rows):
    product = {
        "id": row[0],
        "name": row[1],
        "price": row[2],
        "image_path": row[3]
    }

    card = ProductCard(product)
    self.cards_layout.addWidget(card, index // 3, index % 3)
\`\`\`

Разберём:

- \`rows\` — список товаров, полученный из БД;
- \`enumerate(rows)\` — перебирает список и дополнительно даёт индекс;
- \`index\` — номер текущего товара: 0, 1, 2, 3 и т. д.;
- \`row\` — данные текущего товара;
- \`ProductCard(product)\` — создаёт новый виджет карточки;
- \`addWidget()\` — помещает карточку в Layout.

**Почему карточки создаются динамически?** Потому что заранее неизвестно, сколько строк вернёт запрос к БД. Цикл создаст ровно столько карточек, сколько товаров пришло.

## 6.2. Как работает index // 3 и index % 3

Если хотим три карточки в одной строке:

- \`index // 3\` вычисляет номер строки;
- \`index % 3\` вычисляет номер колонки.

Пример:

| index | index // 3 (строка) | index % 3 (колонка) |
|---:|---:|---:|
| 0 | 0 | 0 |
| 1 | 0 | 1 |
| 2 | 0 | 2 |
| 3 | 1 | 0 |
| 4 | 1 | 1 |
| 5 | 1 | 2 |

Получается:

\`\`\`text
┌──────────┬──────────┬──────────┐
│ Товар 1  │ Товар 2  │ Товар 3  │
├──────────┼──────────┼──────────┤
│ Товар 4  │ Товар 5  │ Товар 6  │
├──────────┼──────────┼──────────┤
│ Товар 7  │ Товар 8  │ Товар 9  │
└──────────┴──────────┴──────────┘
\`\`\`

Хочешь две колонки — замени число 3 на 2. Хочешь четыре — на 4.

## 6.3. Если нужна не сетка, а список

В текущем проекте карточки размещаются вертикально, одна под другой. Для этого вместо \`QGridLayout\` можно использовать \`QVBoxLayout\`:

\`\`\`python
self.cards_layout = QVBoxLayout(self.cards_container)
self.cards_layout.setAlignment(
    Qt.AlignmentFlag.AlignTop
)

for product in products:
    card = ProductCard(product)
    self.cards_layout.addWidget(card)
\`\`\`

- \`QVBoxLayout\` — сверху вниз;
- \`QHBoxLayout\` — слева направо;
- \`QGridLayout\` — строки и колонки.

Для каталога с карточками одинакового размера часто удобен \`QGridLayout\`. Для широких горизонтальных карточек, как в текущем \`MyWin.add_cards()\`, подходит \`QVBoxLayout\` с \`QHBoxLayout\` внутри каждой карточки.

---

# 7. QScrollArea: зачем она нужна

Если товаров больше, чем помещается на экране, нужен скролл.

Правильная базовая конструкция:

\`\`\`python
self.cards_container = QWidget()
self.cards_layout = QGridLayout(self.cards_container)

self.scroll = QScrollArea()
self.scroll.setWidgetResizable(True)
self.scroll.setWidget(self.cards_container)

main_layout.addWidget(self.scroll)
\`\`\`

Запомни три объекта:

1. \`QScrollArea\` — область, которая прокручивается.
2. \`cards_container\` — содержимое, которое находится внутри области.
3. \`cards_layout\` — место, куда добавляются карточки.

Карточки добавляем именно в \`cards_layout\`, а не прямо в \`QScrollArea\`.

---

# 8. Как очистить старые карточки и загрузить каталог заново

Например, пользователь выбрал категорию или перешёл на другую страницу. Нельзя просто повторно вызвать \`load_products()\`: иначе старые карточки останутся, а новые добавятся поверх/ниже.

Для \`QGridLayout\` подойдёт такая функция:

\`\`\`python
def clear_cards(self):
    while self.cards_layout.count():
        item = self.cards_layout.takeAt(0)

        widget = item.widget()
        if widget is not None:
            widget.deleteLater()
\`\`\`

Что происходит:

- \`count()\` — сколько элементов сейчас находится в Layout;
- \`takeAt(0)\` — забирает первый элемент из Layout;
- \`widget()\` — возвращает виджет внутри элемента;
- \`deleteLater()\` — просит Qt удалить виджет безопасным способом.

После очистки можно снова добавить карточки:

\`\`\`python
def load_products(self):
    self.clear_cards()

    products = self.db.get_products()

    for index, row in enumerate(products):
        product = {
            "id": row[0],
            "name": row[1],
            "price": row[2],
            "image_path": row[3]
        }

        card = ProductCard(product)
        card.clicked.connect(self.open_product)

        self.cards_layout.addWidget(
            card,
            index // 3,
            index % 3
        )
\`\`\`

В текущем проекте уже есть похожий метод \`MainWidget.clear_cards()\`. Он очищает вертикальный Layout каталога.

Если внутри Layout есть вложенные Layout, для полной очистки понадобится рекурсивно обработать и их. Для обычной сетки карточек достаточно примера выше.

---

# 9. Как показать подробную информацию о товаре

Есть два простых способа.

## Способ 1. Передать товар в отдельное окно

\`\`\`python
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout


class ProductDetails(QWidget):
    def __init__(self, product):
        super().__init__()

        self.setWindowTitle("Информация о товаре")
        self.resize(350, 300)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(product["name"]))
        layout.addWidget(QLabel(f'Цена: {product["price"]} ₽'))
        layout.addWidget(QLabel(f'ID: {product["id"]}'))
\`\`\`

В главном окне:

\`\`\`python
def open_product(self, product):
    self.details_window = ProductDetails(product)
    self.details_window.show()
\`\`\`

Сохраняем окно в \`self.details_window\`, чтобы на него оставалась ссылка, пока оно открыто.

## Способ 2. Получить полные данные из БД по ID

Иногда в карточке показывается только краткая информация. При клике можно запросить остальные поля:

\`\`\`python
def open_product(self, product):
    full_product = self.db.get_product_by_id(product["id"])

    if full_product is None:
        return

    self.details_window = ProductDetails(full_product)
    self.details_window.show()
\`\`\`

Здесь \`product["id"]\` нужен, чтобы найти товар в БД. Не нужно передавать в SQL название товара: ID обычно однозначно определяет запись.

---

# 10. Как подключать кнопки и обрабатывать клики

В PyQt6 кнопка имеет сигнал \`clicked\`.

\`\`\`python
button.clicked.connect(self.some_method)
\`\`\`

Читается так: когда пользователь нажмёт кнопку, вызови метод \`some_method\`.

Пример:

\`\`\`python
self.button = QPushButton("Подробнее")
self.button.clicked.connect(self.show_details)

def show_details(self):
    print("Нажали кнопку")
\`\`\`

## Если обработчику нужны данные конкретного товара

Можно использовать собственный сигнал карточки, как показано выше:

\`\`\`python
# В ProductCard
clicked = pyqtSignal(object)

def on_click(self):
    self.clicked.emit(self.product)
\`\`\`

\`\`\`python
# В MainWindow
card.clicked.connect(self.open_product)

def open_product(self, product):
    print(product["id"], product["name"])
\`\`\`

Так надёжнее и понятнее, чем пытаться обращаться к переменной цикла из обработчика позже.

---

# 11. Как адаптировать это под текущий проект SPORTWEAR

В репозитории уже есть рабочие заготовки, и их не нужно переписывать с нуля.

## Что уже реализовано

### \`db_units/qwersql.py\`

Класс \`QwerSql\`:
- подключается к PostgreSQL через \`psycopg2\`;
- содержит \`show_products(page)\`;
- получает количество товаров через \`count_products()\`;
- вычисляет количество страниц через \`total_pages()\`;
- получает данные пользователя и обновляет их.

То есть роль этого класса уже совпадает с ролью предлагаемого \`Database\` / \`config.py\`.

### \`ui_units/main_widget.py\`

Класс \`MainWidget\`:
- создаёт \`QScrollArea\`;
- создаёт внутренний контейнер;
- создаёт Layout;
- содержит \`clear_cards()\`.

Это отдельная область каталога. Её можно оставить как есть.

### \`texshopProductShow.py\`

Класс \`MyWin\`:
- создаёт главное окно;
- создаёт объект \`QwerSql\`;
- вызывает \`render_page()\`;
- получает строки из БД;
- превращает строку в словарь \`data\`;
- вызывает \`add_cards(data)\`;
- добавляет карточки в \`MainWidget\`.

Самая важная часть текущей реализации:

\`\`\`python
def render_page(self):
    self.main_widget.clear_cards()
    self.total_pages = self.db.total_pages()

    for row in self.db.show_products(self.current_page):
        (
            product_id, name, category, type_,
            brand, material, size, color,
            quantity, price, discount, image_path
        ) = row

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
\`\`\`

Разбор:
1. Очищаем предыдущие карточки.
2. Получаем строки текущей страницы.
3. Распаковываем кортеж в понятные переменные.
4. Собираем словарь \`data\`.
5. Передаём словарь в метод создания карточки.

**Почему словарь удобнее кортежа?** После преобразования можно написать \`data["name"]\`, а не запоминать, что название лежит в \`row[1]\`, а цена — в \`row[9]\`.

Текущий \`add_cards(data)\` создаёт горизонтальную карточку из \`QWidget\`, \`QHBoxLayout\`, \`QLabel\` и изображения. Это вполне нормальный и понятный вариант для контрольной. Если карточек много и разметка повторяется, вынеси её в класс \`ProductCard\`.

## Какой вариант выбрать на контрольной

Если задача — быстро вывести товары:
1. Подключить БД.
2. Вызвать метод получения товаров.
3. Перебрать результат циклом.
4. Для каждой строки создать \`QWidget\` / \`ProductCard\`.
5. Создать QLabel с названием и ценой.
6. Загрузить фото через \`QPixmap\`.
7. Добавить карточку в Layout.

Если задача требует переиспользуемую карточку или обработку кликов — отдельный класс \`ProductCard(QWidget)\` будет лучше.

---

# 12. Самый короткий шаблон для контрольной

Если времени мало, запомни эту последовательность.

## 1. Получить товары

\`\`\`python
products = self.db.get_products()
\`\`\`

## 2. Перебрать товары

\`\`\`python
for index, product in enumerate(products):
    ...
\`\`\`

## 3. Создать карточку

\`\`\`python
card = ProductCard(product)
\`\`\`

## 4. Загрузить картинку

\`\`\`python
pixmap = QPixmap(image_path)
label.setPixmap(
    pixmap.scaled(
        150, 150,
        Qt.AspectRatioMode.KeepAspectRatio
    )
)
\`\`\`

## 5. Подключить клик

\`\`\`python
card.clicked.connect(self.open_product)
\`\`\`

## 6. Добавить в Layout

\`\`\`python
self.cards_layout.addWidget(
    card,
    index // 3,
    index % 3
)
\`\`\`

## 7. Очистить перед повторной загрузкой

\`\`\`python
while self.cards_layout.count():
    item = self.cards_layout.takeAt(0)
    if item.widget():
        item.widget().deleteLater()
\`\`\`

---

# 13. Частые ошибки

| Ошибка | Почему | Что делать |
|---|---|---|
| Картинка не отображается | Неправильный путь | Проверить \`image_path\`, рабочую папку и \`pixmap.isNull()\` |
| Карточки не появляются | Не вызван \`addWidget()\` | Добавить карточку в Layout |
| Все карточки показывают один товар | Используются общие/перезаписываемые данные | Передавать конкретный \`product\` в конструктор каждой карточки |
| После обновления товары дублируются | Старые виджеты не удаляются | Перед загрузкой вызвать \`clear_cards()\` |
| \`KeyError: 'name'\` | В словаре нет ключа \`name\` | Проверить, как сформирован словарь |
| \`IndexError\` | В кортеже нет элемента с таким индексом | Проверить SELECT и порядок колонок |
| \`TypeError\` при addWidget | Передан не тот тип аргумента | Для сетки передавать виджет, номер строки и колонки |
| Кнопка ничего не делает | Не подключён сигнал | Использовать \`button.clicked.connect(...)\` |
| Ошибка SQL около значения | Неправильно собрана строка запроса | Передавать параметры через \`%s\` |
| После закрытия приложения соединение остаётся | Не закрыта БД | Вызвать \`self.db.close()\` при закрытии окна |

---

# 14. Что нужно выучить в первую очередь

Для практической контрольной особенно важно уверенно понимать эти конструкции:

| Конструкция | Что делает |
|---|---|
| \`QWidget\` | Создаёт виджет/контейнер |
| \`QLabel\` | Показывает текст или изображение |
| \`QPushButton\` | Создаёт кнопку |
| \`QVBoxLayout\` | Располагает элементы вертикально |
| \`QHBoxLayout\` | Располагает элементы горизонтально |
| \`QGridLayout\` | Располагает элементы в таблице |
| \`QScrollArea\` | Добавляет прокрутку |
| \`QPixmap\` | Загружает изображение |
| \`setPixmap()\` | Устанавливает изображение в QLabel |
| \`scaled()\` | Меняет размер изображения |
| \`clicked.connect()\` | Подключает обработчик нажатия |
| \`pyqtSignal()\` | Создаёт собственный сигнал |
| \`addWidget()\` | Добавляет виджет в Layout |
| \`fetchall()\` | Получает все строки SQL-запроса |
| \`fetchone()\` | Получает одну строку |
| \`enumerate()\` | Даёт индекс и элемент при переборе |
| \`self.product = product\` | Сохраняет данные товара в конкретном объекте |

## Универсальный алгоритм решения задачи

Когда на контрольной просят сделать каталог товаров, действуй в таком порядке:

1. Создай подключение к БД и метод \`get_products()\`.
2. Создай главное окно и центральный \`QWidget\`.
3. Назначь ему \`QVBoxLayout\` или \`QGridLayout\`.
4. Если товаров много — помести контейнер в \`QScrollArea\`.
5. Получи список товаров из БД.
6. Перебери список через \`for\` или \`enumerate\`.
7. Для каждого товара создай карточку.
8. Добавь в неё фото, название, цену и кнопку.
9. Подключи кнопку через \`clicked.connect()\`.
10. Добавь карточку в Layout.
11. Перед повторной загрузкой очисти старые карточки.
12. При закрытии приложения закрой соединение с БД.

**Если запомнить одну мысль:** БД возвращает данные, главное окно перебирает их и создаёт карточки, карточка отвечает за то, как выглядит один товар. Это простая архитектура, которую легко воспроизвести на контрольной и расширить позже.
