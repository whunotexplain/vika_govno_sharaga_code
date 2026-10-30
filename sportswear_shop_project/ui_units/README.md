# Подробный разбор main_widget.py — PyQt6 на примере магазина SPORTWEAR

Это руководство объясняет **каждый класс из файла `ui_units/main_widget.py`**, зачем он нужен, как устроен и как взаимодействует с главным окном `MyWin`, базой данных `QwerSql` и пользователем.

Материал рассчитан на подготовку к практической контрольной: цель не просто скопировать код, а научиться узнавать типовые конструкции и самостоятельно писать похожие окна для другой предметной области.

Исходный файл: [ui_units/main_widget.py](https://github.com/whunotexplain/vika_govno_sharaga_code/blob/main/sportswear_shop_project/ui_units/main_widget.py)

Связанные файлы:
- [texshopProductShow.py — главное окно и логика приложения](../texshopProductShow.py)
- [qwersql.py — методы PostgreSQL](../db_units/qwersql.py)

---

# 1. Общая архитектура: кто с кем связан

В приложении есть три уровня:

1. **UI-классы** — создают окна, поля, кнопки, картинки и формы.
2. **Главное окно `MyWin`** — управляет приложением: открывает окна, реагирует на клики, получает данные, переключает страницы.
3. **Класс `QwerSql`** — выполняет SQL-запросы к PostgreSQL.

Упрощённая схема:

~~~text
ПОЛЬЗОВАТЕЛЬ
    |
    | нажал кнопку / выбрал товар / ввёл пароль
    v
UI-КЛАСС из main_widget.py
    |
    | сигнал clicked.connect(...)
    v
МЕТОД ГЛАВНОГО ОКНА MyWin
    |
    | вызывает метод базы
    v
QwerSql
    |
    | SQL-запрос
    v
PostgreSQL
    |
    | результат SELECT / результат UPDATE
    v
QwerSql возвращает данные
    |
    v
MyWin передаёт данные в UI-виджет
    |
    v
ПОЛЬЗОВАТЕЛЬ ВИДИТ РЕЗУЛЬТАТ
~~~

**Главное правило:** UI-класс обычно отвечает за внешний вид и хранение виджетов. Главное окно решает, что делать при действии пользователя. Класс БД отвечает за SQL.

Например:
- `Auth` создаёт поля логина и пароля.
- `MyWin.entry_win()` открывает окно авторизации и получает результат.
- `Auth.show_page1()` проверяет введённые данные через `QwerSql`.
- `QwerSql.get_auth()` выполняет SELECT.
- Если пользователь найден, `Auth` вызывает `accept()`.
- `MyWin` видит `Accepted` и запоминает ID пользователя.

---

# 2. Что означают импорты

Исходный файл начинается так:

~~~python
from PyQt6.QtWidgets import *
from PyQt6 import QtCore, QtGui
from db_units.qwersql import QwerSql
~~~

- `PyQt6.QtWidgets` — готовые элементы интерфейса: `QWidget`, `QLabel`, `QPushButton`, `QLineEdit`, `QScrollArea`, `QDialog`, layouts и другие.
- `QtCore` — базовые перечисления и механизмы Qt: выравнивание, курсор, формат текста и т. д.
- `QtGui` — графические объекты, в данном проекте, например, `QPixmap` для изображения.
- `QwerSql` — наш класс, который умеет обращаться к PostgreSQL.

Звёздочка в `from PyQt6.QtWidgets import *` импортирует много имён сразу. Для учебного проекта это коротко, но в большом проекте лучше явно перечислять используемые классы.

Ниже в файле повторяются импорты PyQt6. Повторный импорт обычно не ломает программу, но он избыточен: достаточно импортировать нужные классы один раз в начале файла.

---

# 3. Класс MainWidget — контейнер со скроллом

## 3.1. Для чего нужен этот класс

`MainWidget` — отдельный виджет, внутри которого находится прокручиваемая область. В неё главное окно динамически добавляет карточки товаров.

Представь каталог интернет-магазина: товаров может быть 100, а окно показывает только несколько. Пользователь прокручивает список колесом мыши.

В главном окне он создаётся так:

~~~python
self.main_widget = MainWidget()
main_layout.addWidget(self.main_widget, 1)
~~~

То есть `MyWin` не обязано знать, как именно устроен скролл. Оно просто добавляет готовый `MainWidget` в свой layout.

## 3.2. Разбор конструктора построчно

Исходный код:

~~~python
class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.scroll_area_widget = QWidget()
        self.scroll_area_widget_layout = QVBoxLayout(self.scroll_area_widget)
        self.scroll_area_widget_layout.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignTop
        )
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_area_widget)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.scroll_area)
~~~

### Строка 1. Наследование

~~~python
class MainWidget(QWidget):
~~~

Создаём собственный класс `MainWidget` на основе `QWidget`.

`QWidget` — базовый универсальный виджет. Он может быть самостоятельным окном или частью другого окна. Мы используем его как контейнер.

Почему не `QMainWindow`? Потому что это не главное окно приложения, а вложенная часть интерфейса. Для таких блоков обычно подходит `QWidget`.

### Строка 2. Конструктор

~~~python
def __init__(self):
    super().__init__()
~~~

`__init__` выполняется при создании объекта:

~~~python
self.main_widget = MainWidget()
~~~

`super().__init__()` запускает конструктор родительского `QWidget`. Он подготавливает внутреннюю часть Qt. В наследуемых классах Qt почти всегда начинай конструктор с этой строки.

### Строка 3. Внутренний контейнер

~~~python
self.scroll_area_widget = QWidget()
~~~

Создаём обычный пустой виджет. Он будет **содержимым прокручиваемой области**.

Зачем нужен ещё один QWidget? Потому что `QScrollArea` прокручивает один дочерний виджет. Мы помещаем в него контейнер, а уже в контейнер добавляем много карточек.

Запомни разницу:

- `scroll_area` — рамка/область, которая умеет прокручиваться;
- `scroll_area_widget` — длинное содержимое внутри этой области;
- карточки — дочерние элементы внутри содержимого.

### Строка 4. Layout для карточек

~~~python
self.scroll_area_widget_layout = QVBoxLayout(self.scroll_area_widget)
~~~

Создаём вертикальный layout и назначаем его контейнеру `scroll_area_widget`.

`QVBoxLayout` размещает элементы сверху вниз:

~~~text
┌─────────────────────────┐
│ Карточка 1              │
├─────────────────────────┤
│ Карточка 2              │
├─────────────────────────┤
│ Карточка 3              │
├─────────────────────────┤
│ Карточка 4              │
└─────────────────────────┘
~~~

Именно в этот layout позже будут добавляться карточки:

~~~python
self.main_widget.scroll_area_widget_layout.addWidget(card)
~~~

### Строка 5. Выравнивание по верхнему краю

~~~python
self.scroll_area_widget_layout.setAlignment(
    QtCore.Qt.AlignmentFlag.AlignTop
)
~~~

Говорим layout: располагай элементы от верхнего края.

Без этого при небольшом количестве карточек содержимое может визуально располагаться не так, как ожидается. Для каталога обычно удобно начинать список сверху.

### Строка 6. Создание прокручиваемой области

~~~python
self.scroll_area = QScrollArea()
~~~

`QScrollArea` — виджет Qt, который показывает часть большого содержимого и позволяет прокручивать его.

Аналогия: это окно в длинный список. Сам список может быть выше видимой части окна.

### Строка 7. Изменение размера содержимого

~~~python
self.scroll_area.setWidgetResizable(True)
~~~

Разрешаем содержимому подстраиваться под размер области прокрутки.

Если значение `True`, дочерний виджет может растягиваться под доступную ширину/размер. Это помогает карточкам занимать ширину каталога.

Важно: эта команда не создаёт прокрутку сама по себе. Она управляет изменением размера дочернего виджета.

### Строка 8. Помещаем содержимое внутрь QScrollArea

~~~python
self.scroll_area.setWidget(self.scroll_area_widget)
~~~

Это ключевая связь.

Мы говорим: «Вот этот `scroll_area_widget` является содержимым моей прокручиваемой области».

До этой строки у нас существуют два отдельных виджета. После неё внутренний контейнер становится содержимым `QScrollArea`.

### Строка 9. Layout самого MainWidget

~~~python
self.main_layout = QVBoxLayout(self)
~~~

Создаём layout для внешнего `MainWidget`. Он нужен, чтобы расположить саму область прокрутки внутри `MainWidget`.

Обрати внимание: здесь layout назначается `self`, то есть текущему объекту `MainWidget`.

### Строка 10. Добавляем скролл в основной layout

~~~python
self.main_layout.addWidget(self.scroll_area)
~~~

Теперь `QScrollArea` занимает пространство `MainWidget`.

## 3.3. Вся конструкция QScrollArea на схеме

~~~text
MyWin — главное окно
  |
  +-- main_layout
        |
        +-- MainWidget
              |
              +-- main_layout
                    |
                    +-- QScrollArea
                          |
                          +-- scroll_area_widget
                                |
                                +-- QVBoxLayout
                                      |
                                      +-- карточка 1
                                      +-- карточка 2
                                      +-- карточка 3
                                      +-- карточка 4
~~~

**Почему не добавлять карточки напрямую в QScrollArea?**

Потому что `QScrollArea` предназначена для одного внутреннего виджета. Много элементов удобнее размещать в layout этого внутреннего виджета.

## 3.4. Метод clear_cards() — очистка старых карточек

Исходный код:

~~~python
def clear_cards(self):
    while self.scroll_area_widget_layout.count():
        item = self.scroll_area_widget_layout.takeAt(0)
        widget = item.widget()
        if widget:
            widget.deleteLater()
~~~

Этот метод удаляет карточки из layout перед тем, как показать новые.

Разберём каждую строку.

**1. Проверяем, есть ли элементы:**

~~~python
while self.scroll_area_widget_layout.count():
~~~

`count()` возвращает количество элементов в layout.

Почему `while`, а не `if`? Потому что нужно убрать все карточки, а не только одну.

**2. Забираем первый элемент:**

~~~python
item = self.scroll_area_widget_layout.takeAt(0)
~~~

`takeAt(0)` извлекает элемент с индексом 0 из layout. После этого он больше не числится в layout.

Важно: извлечь элемент из layout и уничтожить сам виджет — не одно и то же. Поэтому дальше отдельно получаем виджет и удаляем его.

**3. Получаем сам виджет:**

~~~python
widget = item.widget()
~~~

`item` — объект элемента layout. Метод `widget()` возвращает виджет, который находился в этом элементе.

**4. Проверяем и планируем удаление:**

~~~python
if widget:
    widget.deleteLater()
~~~

Если внутри элемента действительно есть виджет, вызываем `deleteLater()`.

Это безопасный для Qt способ запланировать удаление объекта после обработки текущих событий. Он не равен простому удалению элемента из layout.

### Зачем очищать карточки?

Посмотри на метод `render_page()` в главном окне:

~~~python
def render_page(self):
    self.main_widget.clear_cards()

    for row in self.db.show_products(self.current_page):
        # подготовка data
        self.add_cards(data)
~~~

При переходе на следующую страницу сначала удаляются карточки предыдущей страницы, потом создаются новые.

Если не вызвать `clear_cards()`, старые карточки останутся, а новые добавятся ниже. Пользователь увидит смешанные данные нескольких страниц.

### Универсальный шаблон ScrollArea для контрольной

~~~python
class ListWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.container)

        layout = QVBoxLayout(self)
        layout.addWidget(self.scroll)

    def add_item(self, widget):
        self.container_layout.addWidget(widget)

    def clear_items(self):
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
~~~

Для другой задачи меняй название `ListWidget` и добавляемые элементы. Принцип остаётся тем же.

---

# 4. Класс NextWin — окно подробной информации о товаре

## 4.1. Назначение

`NextWin` открывает отдельное окно, где пользователь видит подробную информацию о выбранном товаре и его изображение.

Класс наследуется от `QWidget`, потому что это обычное окно, а не диалог с результатом Accepted/Rejected.

Создаётся в главном окне:

~~~python
def open_details(self, data):
    self.next_win = NextWin(data)
    self.next_win.show()
~~~

Обрати внимание на `NextWin(data)`: главное окно передаёт словарь с данными товара в конструктор нового окна.

## 4.2. Конструктор и аргумент data

~~~python
class NextWin(QWidget):
    def __init__(self, data):
        super().__init__()
        self.resize(360, 420)
        self.setWindowTitle("Информация о товаре")
~~~

- `data` — словарь, содержащий информацию о конкретном товаре.
- `resize(360, 420)` — задаёт размер окна.
- `setWindowTitle(...)` — задаёт заголовок.

Пример словаря:

~~~python
data = {
    "img": "resources/products/shirt.png",
    "name": "Футболка",
    "category": "Одежда",
    "type": "Спортивная",
    "manufacturing": "Nike",
    "cloth": "Хлопок",
    "size": "M",
    "color": "Чёрный",
    "quantity": 10,
    "price": 2500,
    "discount": 15
}
~~~

Почему передаём словарь, а не десять отдельных аргументов? Так удобнее группировать связанные значения и передавать их одним объектом.

## 4.3. Создание layout

~~~python
layout = QVBoxLayout(self)
~~~

Создаём вертикальную компоновку прямо для окна `NextWin`.

Дальше элементы, добавленные через `layout.addWidget(...)`, будут располагаться сверху вниз.

## 4.4. Создание QLabel для изображения

~~~python
lbl_image = QLabel()
lbl_image.setAlignment(
    QtCore.Qt.AlignmentFlag.AlignCenter
)
~~~

`QLabel` может показывать текст или изображение.

Сначала создаём пустую метку, затем центрируем её содержимое.

## 4.5. Получение пути к картинке

~~~python
image_path = data.get("img", "")
~~~

`dict.get(key, default)` получает значение по ключу. Если ключа нет, возвращает значение по умолчанию — пустую строку.

Отличие от `data["img"]`: если ключ отсутствует, квадратные скобки вызовут `KeyError`, а `get()` спокойно вернёт значение по умолчанию.

## 4.6. Абсолютный и относительный путь

~~~python
if image_path and not os.path.isabs(image_path):
    image_path = os.path.join(BASE_DIR, image_path)
~~~

- `image_path` — путь, который пришёл из словаря.
- `os.path.isabs(...)` проверяет, абсолютный ли путь.
- `not` означает «если путь НЕ абсолютный».
- `os.path.join(...)` соединяет базовую папку проекта и относительный путь.

Относительный путь: `resources/products/shirt.png`.

Абсолютный путь в Windows может выглядеть так: `C:\\project\\resources\\shirt.png`.

Почему это важно? Если приложение запускается из другой рабочей папки, относительный путь может перестать находить изображение. Привязка к папке проекта делает поиск предсказуемее.

В файле `main_widget.py` базовая папка вычисляется так:

~~~python
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
~~~

- `__file__` — путь к текущему файлу.
- `abspath()` — превращает его в абсолютный путь.
- первый `dirname()` поднимается из `ui_units` в папку проекта;
- второй `dirname()` поднимается ещё на уровень выше.

**Внимание:** точка отсчёта зависит от того, где лежит файл. Поэтому при переносе кода всегда проверяй, к какой папке приводит BASE_DIR.

## 4.7. Загрузка изображения

~~~python
pix = QtGui.QPixmap(image_path)
~~~

`QPixmap` загружает изображение из файла в объект, который Qt умеет отображать.

Проверка:

~~~python
if not pix.isNull():
~~~

Если `isNull()` вернул False, изображение загрузилось успешно. Если объект пустой, файл не найден, путь неверный или формат не удалось прочитать.

Успешная загрузка:

~~~python
lbl_image.setPixmap(
    pix.scaled(
        220, 220,
        QtCore.Qt.AspectRatioMode.KeepAspectRatio,
        QtCore.Qt.TransformationMode.SmoothTransformation
    )
)
~~~

- `scaled(220, 220)` — ограничивает изображение размером 220×220.
- `KeepAspectRatio` — сохраняет пропорции, чтобы картинка не растягивалась.
- `SmoothTransformation` — использует сглаживание при масштабировании.
- `setPixmap()` — помещает изображение в QLabel.

Если изображение не загрузилось:

~~~python
else:
    lbl_image.setText("Изображение отсутствует")
    print("Не найдено изображение:", image_path)
~~~

Пользователь увидит сообщение, а разработчик получит путь в консоли.

## 4.8. Вывод информации о товаре

~~~python
layout.addWidget(lbl_image)

text = (
    f"Название: {data['name']}\\n"
    f"Категория: {data['category']}\\n"
    f"Тип: {data['type']}\\n"
    f"Бренд: {data['manufacturing']}\\n"
    f"Материал: {data['cloth']}\\n"
    f"Размер: {data['size']}\\n"
    f"Цвет: {data['color']}\\n"
    f"Количество: {data['quantity']}\\n"
    f"Цена: {data['price']} ₽\\n"
    f"Скидка: {data['discount']}%"
)

label = QLabel(text)
label.setWordWrap(True)
layout.addWidget(label)
~~~

Здесь:
- `f"...{...}"` — f-строка, подставляет значение переменной или выражения;
- `\\n` — перенос строки;
- `QLabel(text)` — метка с готовым текстом;
- `setWordWrap(True)` — разрешает переносить длинный текст;
- `addWidget()` — добавляет метку в окно.

### Как написать похожее окно для любой сущности

Например, для студента:

~~~python
class StudentDetails(QWidget):
    def __init__(self, data):
        super().__init__()
        self.setWindowTitle("Информация о студенте")
        layout = QVBoxLayout(self)

        text = (
            f"ФИО: {data['name']}\\n"
            f"Группа: {data['group']}\\n"
            f"Средний балл: {data['grade']}"
        )

        layout.addWidget(QLabel(text))
~~~

Меняется словарь и подписи. Приём тот же.

---

# 5. Класс Auth — окно авторизации

Это один из самых важных классов для контрольной. Здесь видно, как UI получает данные, проверяет их и взаимодействует с БД.

## 5.1. Почему Auth наследуется от QDialog

~~~python
class Auth(QDialog):
~~~

`QDialog` — диалоговое окно. Оно обычно выполняет отдельное действие: вход, подтверждение, ввод параметров, смена пароля.

В отличие от обычного `QWidget`, диалог имеет результат завершения:
- `accept()` — пользователь успешно завершил действие;
- `reject()` — отменил действие;
- `exec()` — показывает диалог в модальном режиме и возвращает результат после его закрытия.

## 5.2. Создание окна

~~~python
class Auth(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Вход — SPORTWEAR")
        self.resize(420, 180)
        self.setModal(True)
        self.auth_data = None
~~~

- `super().__init__()` — инициализация QDialog.
- `setWindowTitle()` — заголовок.
- `resize()` — размер.
- `setModal(True)` — окно модальное: пока диалог открыт, пользователь не может взаимодействовать с родительским окном.
- `self.auth_data = None` — заранее создаём атрибут для результата авторизации.

Почему `None`? Пока пользователь не прошёл проверку, данных авторизованного пользователя нет.

После успешного входа здесь будет словарь, например:

~~~python
{"id": 7, "name": "Иван"}
~~~

## 5.3. Layout и форма

~~~python
layout = QVBoxLayout(self)
form = QFormLayout()
~~~

- `QVBoxLayout` — вертикально размещает основные элементы.
- `QFormLayout` — специальный layout для формы «подпись + поле».

Визуально:

~~~text
┌─────────────────────────────────┐
│ Вход — SPORTWEAR                 │
│                                 │
│ Логин:   [___________________]  │
│ Пароль:  [___________________]  │
│                                 │
│          [ Войти ]              │
│ Демо-доступ: demo / demo123     │
└─────────────────────────────────┘
~~~

## 5.4. Поле логина

~~~python
self.le_login = QLineEdit()
self.le_login.setPlaceholderText("Логин")
~~~

`QLineEdit` — однострочное поле ввода.

`setPlaceholderText()` задаёт подсказку внутри пустого поля. Это не значение пользователя, а только визуальная подсказка.

## 5.5. Поле пароля

~~~python
self.le_passw = QLineEdit()
self.le_passw.setPlaceholderText("Пароль")
self.le_passw.setEchoMode(QLineEdit.EchoMode.Password)
~~~

Это тоже `QLineEdit`, но включён режим скрытия символов.

`EchoMode.Password` показывает точки/звёздочки вместо обычного текста.

Получить реальное значение всё равно можно методом:

~~~python
password = self.le_passw.text()
~~~

## 5.6. Добавление полей в форму

~~~python
form.addRow("Логин:", self.le_login)
form.addRow("Пароль:", self.le_passw)
layout.addLayout(form)
~~~

`addRow()` принимает подпись и виджет. Затем вся форма добавляется в основной вертикальный layout.

## 5.7. Кнопка и связь с методом

~~~python
btn = QPushButton("Войти")
btn.clicked.connect(self.show_page1)
layout.addWidget(btn)
~~~

- `QPushButton` создаёт кнопку.
- `clicked` — сигнал о нажатии.
- `connect(self.show_page1)` — связывает сигнал с методом проверки авторизации.
- `addWidget()` добавляет кнопку в окно.

Важно: передаём `self.show_page1` **без круглых скобок**. Скобки запустили бы метод сразу при создании окна.

## 5.8. Демо-подсказка

~~~python
layout.addWidget(QLabel("Демо-доступ: demo / demo123"))
~~~

Создаём QLabel и сразу добавляем его в layout. Это короткая запись, допустимая в PyQt.

## 5.9. Сам метод show_page1(): полный разбор

Исходный код:

~~~python
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
~~~

Разберём по шагам.

### Шаг 1. Получаем логин и пароль из полей

~~~python
login = self.le_login.text().strip()
password = self.le_passw.text()
~~~

- `text()` возвращает введённую строку.
- `strip()` убирает пробелы в начале и конце логина.

В пароле `strip()` не используется: пробел теоретически может быть частью пароля, поэтому нельзя незаметно менять его значение.

### Шаг 2. Проверяем, что поля заполнены

~~~python
if not login or not password:
    QMessageBox.warning(self, "Предупреждение", "Заполните все поля")
    return
~~~

Условие срабатывает, если логин пустой ИЛИ пароль пустой.

`QMessageBox.warning()` показывает предупреждение.

`return` прекращает метод. Это принципиально: пустые данные не должны отправляться в БД.

### Шаг 3. Обращаемся к базе

~~~python
self.auth_data = QwerSql().get_auth(login, password)
~~~

Здесь происходит цепочка:

1. `QwerSql()` создаёт объект класса доступа к БД.
2. `.get_auth(login, password)` вызывает метод проверки логина и пароля.
3. Метод выполняет SELECT в PostgreSQL.
4. Результат возвращается и сохраняется в `self.auth_data`.

Метод `get_auth()` в `qwersql.py` выполняет запрос примерно такого смысла:

~~~sql
SELECT id, COALESCE(NULLIF(fname, ''), login)
FROM client
WHERE login = %s AND password = %s
LIMIT 1;
~~~

Если пользователь найден, метод возвращает словарь с ID и именем. Если не найден — `None`.

### Шаг 4. Обрабатываем ошибку БД

~~~python
except Exception as exc:
    QMessageBox.critical(self, "Ошибка БД", str(exc))
    return
~~~

Если подключение или запрос завершились ошибкой:
- `exc` содержит объект исключения;
- `str(exc)` превращает его в текст;
- `QMessageBox.critical()` показывает критическую ошибку;
- `return` останавливает метод.

### Шаг 5. Если пользователь найден

~~~python
if self.auth_data:
    self.accept()
~~~

Словарь считается истинным значением. Если `get_auth()` вернул словарь, значит пользователь найден.

`accept()` завершает диалог с результатом Accepted.

### Шаг 6. Если пользователь не найден

~~~python
else:
    QMessageBox.warning(self, "Предупреждение", "Неверный логин или пароль")
~~~

Диалог остаётся открытым, пользователь может попробовать ещё раз.

## 5.10. Как результат Auth получает главное окно

В `MyWin`:

~~~python
def entry_win(self):
    dialog = Auth()

    if dialog.exec() == QDialog.DialogCode.Accepted:
        self.user_id = dialog.auth_data["id"]
        self.menu_bar.show()
        self.btn_login.hide()
~~~

Пошагово:

1. `Auth()` создаёт окно входа.
2. `dialog.exec()` показывает его и ждёт, пока пользователь завершит диалог.
3. Если внутри Auth вызван `accept()`, результат будет `Accepted`.
4. Главное окно забирает ID из `dialog.auth_data["id"]`.
5. Сохраняет его в `self.user_id`.
6. Показывает меню личного кабинета.
7. Скрывает кнопку «Войти».

**Это очень важный принцип:** диалог не обязан сам менять главное окно. Он возвращает результат, а главное окно решает, что делать дальше.

### Вся цепочка авторизации

~~~text
MyWin.entry_win()
      |
      v
dialog = Auth()
      |
      v
dialog.exec() — открыть модальное окно
      |
      v
Пользователь вводит логин и пароль
      |
      v
Нажимает «Войти»
      |
      v
Auth.show_page1()
      |
      +--> пустые поля? показать предупреждение
      |
      v
QwerSql.get_auth(login, password)
      |
      v
SELECT в PostgreSQL
      |
      +--> пользователь не найден
      |        |
      |        v
      |    предупреждение, окно остаётся открытым
      |
      +--> пользователь найден
               |
               v
          self.auth_data = {"id": ..., "name": ...}
               |
               v
          self.accept()
               |
               v
MyWin получает Accepted
               |
               v
self.user_id = dialog.auth_data["id"]
               |
               v
Показывается меню пользователя
~~~

## 5.11. Важное замечание о текущем коде авторизации

В текущем `Auth.show_page1()` создаётся новый объект `QwerSql()` для проверки входа. При этом отдельное соединение явно не закрывается. Для учебного проекта это может работать, но правильнее:
- передавать в Auth уже созданный объект `QwerSql`, или
- использовать отдельное соединение и гарантированно закрывать его.

Кроме того, в текущем SQL пароль сравнивается как обычный текст. Для реального приложения так хранить пароли небезопасно: следует хранить стойкий хэш пароля и проверять его специальной функцией.

---

# 6. Класс AboutUserWidget — интерфейс личного кабинета

## 6.1. Назначение

Этот класс только **создаёт внешний вид профиля**: фото, поля имени, фамилии, почты, телефона и кнопки.

Он сам не загружает профиль из БД и не сохраняет изменения. Этим занимается главное окно `MyWin`.

Создание в главном окне:

~~~python
self.wid_about_user = AboutUserWidget()
self.wid_about_user.hide()
main_layout.addWidget(self.wid_about_user)
~~~

- создаём виджет;
- скрываем его при запуске;
- добавляем в layout главного окна.

Почему сначала hide()? Потому что при запуске показывается каталог, а личный кабинет нужен только после перехода пользователя в соответствующий раздел.

## 6.2. Конструктор

~~~python
class AboutUserWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.main_layout = QVBoxLayout(self)
        self.form_about_user = QFormLayout()
~~~

- `QWidget` — обычный вложенный виджет.
- `QVBoxLayout(self)` — основной вертикальный layout профиля.
- `QFormLayout()` — форма, в которой подпись располагается рядом с полем.

## 6.3. Фото профиля

~~~python
self.lb_photo = QLabel("Фото профиля")
self.lb_photo.setFixedSize(160, 120)
self.lb_photo.setStyleSheet("border: 1px solid gray;")
self.lb_photo.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
self.form_about_user.addRow("Фото", self.lb_photo)
~~~

- `QLabel("Фото профиля")` — метка с текстом.
- `setFixedSize(160, 120)` — фиксированный размер.
- `setStyleSheet(...)` — CSS-подобное оформление Qt.
- `setAlignment(AlignCenter)` — центрирование.
- `addRow()` — добавляет строку формы.

В этом коде это пока заглушка для фото: QLabel показывает текст «Фото профиля», а не загружает фотографию.

## 6.4. Поля профиля

~~~python
self.le_name, self.le_surname = QLineEdit(), QLineEdit()
self.le_email, self.le_phone = QLineEdit(), QLineEdit()
~~~

Создаём четыре поля:
- имя;
- фамилия;
- электронная почта;
- телефон.

Дальше добавляем в форму:

~~~python
self.form_about_user.addRow("Имя", self.le_name)
self.form_about_user.addRow("Фамилия", self.le_surname)
self.form_about_user.addRow("Почта", self.le_email)
self.form_about_user.addRow("Телефон", self.le_phone)
self.main_layout.addLayout(self.form_about_user)
~~~

Обрати внимание: в `addRow()` сначала идёт подпись, потом поле.

## 6.5. Кнопки профиля

~~~python
buttons = QHBoxLayout()
self.bt_edit_pass = QPushButton("Изменить пароль")
self.bt_edit_user_data = QPushButton("Редактировать данные")
buttons.addWidget(self.bt_edit_user_data)
buttons.addWidget(self.bt_edit_pass)
self.main_layout.addLayout(buttons)
~~~

- `QHBoxLayout` располагает кнопки по горизонтали.
- Создаются две кнопки.
- `addWidget()` помещает кнопки в горизонтальный layout.
- `addLayout()` помещает горизонтальный layout в вертикальный layout профиля.

То есть layout можно вкладывать друг в друга.

## 6.6. Кнопка сохранения

~~~python
self.bt_user_data_save = QPushButton("Сохранить")
self.bt_user_data_save.hide()
self.main_layout.addWidget(self.bt_user_data_save)
self.main_layout.addStretch()
~~~

Кнопка «Сохранить» изначально скрыта. Она появляется только в режиме редактирования.

`addStretch()` добавляет растягиваемое свободное пространство, чтобы элементы формы не растягивались на всю высоту и располагались компактнее.

## 6.7. Как главное окно заполняет профиль

В `MyWin.about_user_triggered()`:

~~~python
info = self.db.get_user_info(self.user_id)

if info:
    for key, widget in (
        ("fname", self.wid_about_user.le_name),
        ("lname", self.wid_about_user.le_surname),
        ("email", self.wid_about_user.le_email),
        ("phone", self.wid_about_user.le_phone)
    ):
        widget.setText(info[key])
        widget.setEnabled(False)
~~~

Сначала БД возвращает словарь:

~~~python
{
    "fname": "Иван",
    "lname": "Иванов",
    "email": "ivan@example.com",
    "phone": "+79990000000",
    "id": 7
}
~~~

Затем цикл сопоставляет ключ словаря и конкретное поле интерфейса.

Например:
- `info["fname"]` → `le_name`;
- `info["lname"]` → `le_surname`;
- `info["email"]` → `le_email`;
- `info["phone"]` → `le_phone`.

`setText()` устанавливает значение поля.

`setEnabled(False)` запрещает редактировать поле. Так профиль изначально работает в режиме просмотра.

## 6.8. Как переключается режим редактирования

В главном окне есть метод `edit_user_data()`. На него подключены обе кнопки:

~~~python
self.wid_about_user.bt_edit_user_data.clicked.connect(self.edit_user_data)
self.wid_about_user.bt_user_data_save.clicked.connect(self.edit_user_data)
~~~

Один и тот же метод вызывается:
- при нажатии «Редактировать данные»;
- при нажатии «Сохранить».

Почему один метод? Потому что он проверяет текущее состояние полей и выбирает действие.

~~~python
def edit_user_data(self):
    w = self.wid_about_user

    if not w.le_name.isEnabled():
        # включаем редактирование
        ...
    else:
        # сохраняем
        ...
~~~

`isEnabled()` возвращает True, если поле доступно для взаимодействия.

**Первый режим — просмотр:**
- поля отключены;
- `isEnabled()` возвращает False;
- включаем все поля через `setEnabled(True)`;
- скрываем кнопку редактирования;
- показываем кнопку сохранения.

**Второй режим — редактирование:**
- поля включены;
- `isEnabled()` возвращает True;
- считываем значения;
- вызываем метод БД;
- после успешного сохранения отключаем поля;
- возвращаем кнопку редактирования;
- скрываем кнопку сохранения.

Сохранение:

~~~python
self.db.set_new_user_data(
    w.le_name.text().strip(),
    w.le_surname.text().strip(),
    w.le_email.text().strip(),
    w.le_phone.text().strip(),
    self.user_id
)
~~~

Значения берутся из полей через `text()`, очищаются от пробелов через `strip()`, затем передаются в метод базы.

Метод `set_new_user_data()` выполняет UPDATE:

~~~sql
UPDATE client
SET fname=%s, lname=%s, email=NULLIF(%s, ''), phone=NULLIF(%s, '')
WHERE id=%s;
~~~

Здесь `WHERE id=%s` гарантирует, что обновляется профиль конкретного пользователя, а не все строки.

После запроса метод БД делает `commit()`.

### Обработка ошибки сохранения

~~~python
except Exception as exc:
    self.db.conn.rollback()
    QMessageBox.warning(
        self, "Ошибка", f"Не удалось сохранить данные: {exc}"
    )
    return
~~~

- `except` ловит исключение;
- `rollback()` отменяет незавершённую транзакцию;
- `QMessageBox.warning()` показывает ошибку;
- `return` прекращает метод, не переключая интерфейс в режим просмотра.

---

# 7. Класс PassEditDialog — диалог смены пароля

## 7.1. Назначение

`PassEditDialog` создаёт отдельную форму, в которой пользователь вводит:
1. старый пароль;
2. новый пароль;
3. повтор нового пароля.

Класс отвечает за элементы интерфейса. Проверка введённых значений и обращение к БД находятся в `MyWin.save_user_pass()`.

Наследуется от `QDialog`, потому что это отдельное модальное действие.

## 7.2. Конструктор

~~~python
class PassEditDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Смена пароля")
        self.setModal(True)
~~~

- создаём диалог;
- задаём заголовок;
- делаем окно модальным.

## 7.3. Форма и поля пароля

~~~python
layout = QVBoxLayout(self)
form = QFormLayout()

self.old_pass, self.new1_pass, self.new2_pass = (
    QLineEdit(), QLineEdit(), QLineEdit()
)
~~~

Создаются три однострочных поля. Каждое хранится в атрибуте объекта, поэтому главное окно сможет получить из них значения.

## 7.4. Скрытие символов

~~~python
for field in (self.old_pass, self.new1_pass, self.new2_pass):
    field.setEchoMode(QLineEdit.EchoMode.Password)
~~~

Здесь цикл проходит по трём полям и устанавливает одинаковый режим отображения пароля.

Это лучше, чем три раза писать одну и ту же команду.

## 7.5. Добавление строк формы и кнопки

~~~python
form.addRow("Старый пароль", self.old_pass)
form.addRow("Новый пароль", self.new1_pass)
form.addRow("Повторите новый пароль", self.new2_pass)

self.bt_save_pass = QPushButton("Сохранить")
layout.addLayout(form)
layout.addWidget(self.bt_save_pass)
~~~

Важный момент: кнопка создаётся в диалоге, но её действие подключается в главном окне.

## 7.6. Как главное окно открывает диалог

~~~python
def edit_user_pass(self):
    self.dialog_edit_pass = PassEditDialog()
    self.dialog_edit_pass.bt_save_pass.clicked.connect(
        self.save_user_pass
    )
    self.dialog_edit_pass.exec()
~~~

По шагам:
1. создаём диалог;
2. сохраняем его в `self.dialog_edit_pass`;
3. связываем кнопку сохранения с методом главного окна;
4. показываем диалог через `exec()`.

Почему сохраняем диалог в `self.dialog_edit_pass`, а не в локальную переменную `dialog`? Потому что метод `save_user_pass()` будет обращаться к полям этого диалога. Атрибут `self.dialog_edit_pass` доступен из другого метода главного окна.

## 7.7. Полная логика сохранения нового пароля

~~~python
def save_user_pass(self):
    d = self.dialog_edit_pass

    old_p = d.old_pass.text()
    new1 = d.new1_pass.text()
    new2 = d.new2_pass.text()

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
~~~

Разберём алгоритм.

**Шаг 1. Получаем диалог и значения:**

~~~python
d = self.dialog_edit_pass
old_p = d.old_pass.text()
new1 = d.new1_pass.text()
new2 = d.new2_pass.text()
~~~

`d` — короткая ссылка на диалог. Значения считываются из трёх полей.

**Шаг 2. Проверяем заполнение:**

~~~python
if not old_p or not new1 or not new2:
    ...
    return
~~~

Если хотя бы одно поле пустое, показываем предупреждение и прекращаем выполнение.

**Шаг 3. Проверяем совпадение новых паролей:**

~~~python
if new1 != new2:
    ...
    return
~~~

Оператор `!=` означает «не равно». Если новый пароль и его повтор отличаются, сохранение не выполняется.

**Шаг 4. Проверяем старый пароль:**

~~~python
if not self.db.verify_password(self.user_id, old_p):
    ...
    return
~~~

Вызываем метод БД. Он проверяет, существует ли пользователь с указанным ID и старым паролем.

**Шаг 5. Сохраняем новый пароль:**

~~~python
self.db.update_password(self.user_id, new1)
~~~

Метод БД выполняет UPDATE и commit.

**Шаг 6. Сообщаем об успехе и закрываем диалог:**

~~~python
QMessageBox.information(self, "Успешно", "Пароль изменён")
d.accept()
~~~

`accept()` завершает диалог с результатом Accepted.

В текущем коде стоит дополнительно обернуть обновление пароля в обработку исключений и сделать rollback при ошибке.

---

# 8. Разница между QWidget, QMainWindow и QDialog

Это частый вопрос на защите.

| Класс | Для чего | Пример в проекте |
|---|---|---|
| `QWidget` | Обычный виджет, контейнер или самостоятельное окно | `MainWidget`, `AboutUserWidget`, `NextWin` |
| `QMainWindow` | Главное окно приложения с центральной областью, меню и панелями | `MyWin` |
| `QDialog` | Диалог для отдельного действия с результатом Accepted/Rejected | `Auth`, `PassEditDialog` |

Запомнить просто:
- **QMainWindow** — основное приложение.
- **QWidget** — часть интерфейса или обычное окно.
- **QDialog** — окно-вопрос/форма, которая возвращает результат.

---

# 9. Как классы взаимодействуют друг с другом

## 9.1. Каталог товаров

~~~text
MyWin.__init__()
    |
    v
self.main_widget = MainWidget()
    |
    v
render_page()
    |
    v
self.main_widget.clear_cards()
    |
    v
self.db.show_products(current_page)
    |
    v
для каждой строки создаётся словарь data
    |
    v
add_cards(data)
    |
    v
карточка добавляется в
main_widget.scroll_area_widget_layout
~~~

В `add_cards(data)` главное окно создаёт отдельный QWidget-карточку, добавляет в неё изображение и текст, а затем помещает карточку в layout внутреннего контейнера прокрутки.

## 9.2. Открытие подробной карточки

В `MyWin.add_cards()`:

~~~python
text.mousePressEvent = lambda event, d=data: self.open_details(d)
~~~

Здесь используется lambda, чтобы при клике передать в `open_details()` именно словарь текущего товара.

- `mousePressEvent` — обработчик события нажатия мыши.
- `lambda` — короткая функция.
- `event` — событие мыши, которое Qt передаёт обработчику.
- `d=data` — запоминаем текущий словарь товара.
- `self.open_details(d)` — открываем окно подробностей.

Затем:

~~~python
def open_details(self, data):
    self.next_win = NextWin(data)
    self.next_win.show()
~~~

Создаём окно и передаём данные. `show()` показывает его.

Почему `self.next_win`, а не просто `next_win`? Чтобы ссылка на окно сохранялась как атрибут главного окна. Так объект не потеряется после выхода из метода.

## 9.3. Авторизация

~~~text
Кнопка «Войти»
    |
    v
MyWin.entry_win()
    |
    v
Auth()
    |
    v
dialog.exec()
    |
    v
Auth.show_page1()
    |
    v
QwerSql.get_auth()
    |
    v
PostgreSQL
    |
    v
Auth.accept()
    |
    v
MyWin получает dialog.auth_data["id"]
    |
    v
Меню личного кабинета становится видимым
~~~

## 9.4. Личный кабинет

~~~text
Пункт меню «О пользователе»
    |
    v
MyWin.about_user_triggered()
    |
    +--> проверка self.user_id
    |
    v
QwerSql.get_user_info(user_id)
    |
    v
словарь info
    |
    v
AboutUserWidget: setText()
    |
    v
пользователь видит профиль
~~~

## 9.5. Смена пароля

~~~text
Кнопка «Изменить пароль»
    |
    v
MyWin.edit_user_pass()
    |
    v
PassEditDialog()
    |
    v
пользователь вводит три значения
    |
    v
нажимает «Сохранить»
    |
    v
MyWin.save_user_pass()
    |
    +--> проверка заполнения
    +--> сравнение новых паролей
    +--> проверка старого пароля в БД
    +--> UPDATE нового пароля
    |
    v
dialog.accept()
~~~

---

# 10. Как писать такие классы на контрольной: универсальные заготовки

Не нужно заучивать весь файл. Запомни типовые каркасы.

## 10.1. Простое окно с переданными данными

~~~python
class DetailsWindow(QWidget):
    def __init__(self, data):
        super().__init__()
        self.setWindowTitle("Подробная информация")

        layout = QVBoxLayout(self)
        label = QLabel(data["name"])
        layout.addWidget(label)
~~~

Используй, когда нужно открыть отдельное окно с выбранной записью.

## 10.2. Форма авторизации

~~~python
class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.le_login = QLineEdit()
        self.le_password = QLineEdit()
        self.le_password.setEchoMode(QLineEdit.EchoMode.Password)

        form.addRow("Логин", self.le_login)
        form.addRow("Пароль", self.le_password)
        layout.addLayout(form)

        self.btn_login = QPushButton("Войти")
        self.btn_login.clicked.connect(self.check_login)
        layout.addWidget(self.btn_login)

    def check_login(self):
        login = self.le_login.text().strip()
        password = self.le_password.text()

        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните поля")
            return

        # Здесь вызывается метод БД.
        # Если пользователь найден:
        # self.auth_data = ...
        # self.accept()
~~~

## 10.3. Профиль с редактированием

~~~python
class ProfileWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.le_name = QLineEdit()
        self.le_email = QLineEdit()
        layout.addWidget(self.le_name)
        layout.addWidget(self.le_email)

        self.btn_edit = QPushButton("Редактировать")
        self.btn_save = QPushButton("Сохранить")
        self.btn_save.hide()

        layout.addWidget(self.btn_edit)
        layout.addWidget(self.btn_save)

    def set_profile(self, data):
        self.le_name.setText(data["name"])
        self.le_email.setText(data["email"])
        self.set_editable(False)

    def set_editable(self, enabled):
        self.le_name.setEnabled(enabled)
        self.le_email.setEnabled(enabled)
        self.btn_edit.setVisible(not enabled)
        self.btn_save.setVisible(enabled)
~~~

Здесь `set_profile()` заполняет форму, а `set_editable()` переключает режим.

## 10.4. Диалог с тремя полями

~~~python
class ChangeDialog(QDialog):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.old_value = QLineEdit()
        self.new_value = QLineEdit()
        self.repeat_value = QLineEdit()

        for field in (self.old_value, self.new_value, self.repeat_value):
            field.setEchoMode(QLineEdit.EchoMode.Password)

        form.addRow("Старое значение", self.old_value)
        form.addRow("Новое значение", self.new_value)
        form.addRow("Повтор", self.repeat_value)

        self.btn_save = QPushButton("Сохранить")
        layout.addLayout(form)
        layout.addWidget(self.btn_save)
~~~

---

# 11. Самые важные методы и что они делают

| Метод | Что делает |
|---|---|
| `QVBoxLayout(widget)` | Вертикальный layout для виджета |
| `QHBoxLayout()` | Горизонтальный layout |
| `QFormLayout()` | Форма «подпись + поле» |
| `addWidget(widget)` | Добавляет виджет в layout |
| `addLayout(layout)` | Добавляет layout внутрь другого layout |
| `addRow(label, widget)` | Добавляет строку формы |
| `addStretch()` | Добавляет растягиваемое свободное место |
| `QScrollArea()` | Создаёт область прокрутки |
| `setWidget(widget)` | Назначает внутренний виджет для QScrollArea |
| `setWidgetResizable(True)` | Разрешает изменять размер внутреннего виджета |
| `count()` | Количество элементов в layout |
| `takeAt(index)` | Извлекает элемент из layout |
| `item.widget()` | Получает виджет из элемента layout |
| `deleteLater()` | Планирует удаление виджета |
| `setText(text)` | Устанавливает текст |
| `text()` | Получает текст |
| `setPlaceholderText(text)` | Устанавливает подсказку в поле |
| `setEchoMode(Password)` | Скрывает вводимый пароль |
| `setEnabled(True/False)` | Включает/отключает виджет |
| `isEnabled()` | Проверяет, включён ли виджет |
| `show()` / `hide()` | Показывает / скрывает виджет |
| `setFixedSize(w, h)` | Задаёт фиксированный размер |
| `setAlignment(...)` | Задаёт выравнивание |
| `setWordWrap(True)` | Разрешает перенос текста |
| `setPixmap(pixmap)` | Показывает картинку |
| `QPixmap(path)` | Загружает картинку |
| `isNull()` | Проверяет, удалось ли загрузить изображение |
| `exec()` | Показывает диалог и ждёт его завершения |
| `accept()` | Завершает диалог с результатом Accepted |
| `reject()` | Завершает диалог с результатом Rejected |
| `QMessageBox.warning()` | Показывает предупреждение |
| `QMessageBox.critical()` | Показывает ошибку |
| `QMessageBox.information()` | Показывает информационное сообщение |

---

# 12. Типичные ошибки при написании этих классов

| Ошибка | Почему возникает | Как исправить |
|---|---|---|
| Скролл не прокручивается | Внутренний виджет не назначен через setWidget | Вызвать scroll.setWidget(container) |
| Карточки не видны | Их добавляют не в тот layout | Добавлять в layout внутреннего контейнера |
| Карточки дублируются при смене страницы | Старые элементы не очищаются | Перед добавлением вызвать clear_cards() |
| Атрибут недоступен в другом методе | Виджет создан как локальная переменная | Создать его через self.name |
| Авторизация сразу выполняется при запуске | В connect переданы скобки | Использовать connect(self.method) |
| Диалог закрывается, но вход не выполнен | Не вызван accept() после успешной проверки | Вызвать self.accept() |
| Главное окно не получает ID | Результат не сохранён в self.auth_data | Записать данные перед accept() |
| Пароль виден обычным текстом | Не установлен EchoMode.Password | Вызвать setEchoMode() |
| Изображение не отображается | Неверный путь или файл отсутствует | Проверить путь и pixmap.isNull() |
| Данные профиля не появляются | Не вызван setText() или ключ словаря неверен | Сверить info и поля |
| Сохранение меняет не того пользователя | Нет условия WHERE id = %s | Передавать user_id в UPDATE |
| После ошибки БД запросы не выполняются | Транзакция осталась в состоянии ошибки | Выполнить rollback() |
| Поле не редактируется | setEnabled(False) | Переключить на True |
| Окно подробностей сразу исчезает | Нет сохранённой ссылки на окно | Сохранить его в self.next_win |

---

# 13. Как объяснить преподавателю работу классов

Ниже примеры коротких ответов, которые показывают понимание кода.

**Что делает MainWidget?**

Это пользовательский виджет-контейнер с QScrollArea. Внутри находится отдельный QWidget с вертикальным layout, куда динамически добавляются карточки. Метод clear_cards очищает старые карточки перед загрузкой новой страницы.

**Зачем в QScrollArea нужен дополнительный QWidget?**

QScrollArea прокручивает один внутренний виджет. Поэтому мы создаём контейнер, назначаем его через setWidget(), а уже в layout контейнера размещаем много карточек.

**Что делает NextWin?**

Принимает словарь данных товара, создаёт отдельное окно, загружает изображение через QPixmap и показывает характеристики товара в QLabel.

**Почему Auth наследуется от QDialog?**

Потому что авторизация — отдельное модальное действие. После успешной проверки вызывается accept(), а главное окно получает результат через exec().

**Как происходит авторизация?**

Пользователь вводит логин и пароль. Метод обработчика получает их из QLineEdit, проверяет заполнение и вызывает метод БД. БД выполняет SELECT. Если запись найдена, данные пользователя сохраняются в auth_data и вызывается accept().

**Что делает AboutUserWidget?**

Создаёт интерфейс личного кабинета: фото-заглушку, поля данных и кнопки. Загрузка и сохранение профиля выполняются главным окном.

**Как меняется пароль?**

Открывается PassEditDialog. Главное окно получает три значения, проверяет заполнение, совпадение новых паролей и правильность старого пароля. После этого вызывает UPDATE в БД.

**Зачем использовать self?**

Атрибуты с self принадлежат объекту и доступны из других методов этого же класса. Например, поле self.le_login создаётся в конструкторе, а читается позже в show_page1().

---

# 14. Самопроверка перед контрольной

Попробуй ответить самостоятельно:

1. Чем QWidget отличается от QDialog?
2. Почему MainWidget наследуется от QWidget?
3. Для чего QScrollArea нужен внутренний QWidget?
4. Что делает setWidgetResizable(True)?
5. Что возвращает layout.count()?
6. Чем takeAt(0) отличается от deleteLater()?
7. Почему перед загрузкой следующей страницы нужно очищать карточки?
8. Что делает QPixmap?
9. Для чего проверка isNull()?
10. Как передать данные из одного окна в другое?
11. Что означает QLineEdit.EchoMode.Password?
12. Для чего нужен QFormLayout?
13. Чем show() отличается от exec()?
14. Что возвращает dialog.exec()?
15. В чём разница между accept() и reject()?
16. Как Auth передаёт ID пользователя главному окну?
17. Почему Auth не должен сам показывать меню главного окна?
18. Для чего в профиле используется setEnabled(False)?
19. Как переключить поле в режим редактирования?
20. Почему обработчик смены пароля находится в MyWin, а поля — в PassEditDialog?

---

# 15. Что выучить в первую очередь

Если до контрольной осталось мало времени, приоритет такой:

1. **QWidget + layout:** как создать класс-виджет и разместить в нём элементы.
2. **QScrollArea:** запомнить связку container → layout → scroll.setWidget(container).
3. **QDialog:** понять exec(), accept(), reject().
4. **Авторизация:** поля → text() → проверка → метод БД → auth_data → accept().
5. **Передача данных:** `NextWin(data)`, словари и `self`.
6. **Профиль:** setText(), setEnabled(), text().
7. **Смена пароля:** три поля → проверки → UPDATE → accept().
8. **Очистка динамических элементов:** count() → takeAt() → widget() → deleteLater().

Главная мысль: почти все эти классы состоят из одних и тех же деталей — конструктор, layout, виджеты, сигналы и методы. Если научишься узнавать эти шаблоны, сможешь собрать похожее окно для студентов, сотрудников, книг, заявок или товаров.

---

# 16. Итоговая шпаргалка

~~~python
# 1. Обычный виджет
class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Привет"))

# 2. Диалог
class MyDialog(QDialog):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.btn = QPushButton("Готово")
        layout.addWidget(self.btn)

# 3. Открыть диалог
dialog = MyDialog()
if dialog.exec() == QDialog.DialogCode.Accepted:
    print("Подтверждено")

# 4. Скролл
container = QWidget()
container_layout = QVBoxLayout(container)
scroll = QScrollArea()
scroll.setWidgetResizable(True)
scroll.setWidget(container)

# 5. Добавить карточку
card = QWidget()
container_layout.addWidget(card)

# 6. Очистить карточки
while container_layout.count():
    item = container_layout.takeAt(0)
    widget = item.widget()
    if widget:
        widget.deleteLater()

# 7. Получить текст
value = self.line_edit.text().strip()

# 8. Показать данные
self.line_edit.setText("Иван")

# 9. Скрыть / показать
self.widget.hide()
self.widget.show()

# 10. Заблокировать / разрешить редактирование
self.line_edit.setEnabled(False)
self.line_edit.setEnabled(True)

# 11. Сигнал кнопки
self.button.clicked.connect(self.some_method)

# 12. Успешно завершить диалог
self.accept()
~~~

**Запомни общий принцип:** класс UI создаёт элементы и хранит их в `self`; главное окно связывает действия и логику; класс БД получает параметры и выполняет SQL. Именно это разделение делает код понятным и позволяет быстро адаптировать его под новое задание.
