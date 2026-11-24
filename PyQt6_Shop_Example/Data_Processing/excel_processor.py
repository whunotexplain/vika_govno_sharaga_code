from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXCEL_DIR = ROOT / "Excel_Tables"
SAMPLE_FILE = EXCEL_DIR / "products.xlsx"

def ensure_sample_excel():
    EXCEL_DIR.mkdir(exist_ok=True)
    if not SAMPLE_FILE.exists():
        data = [
            ("Беспроводная мышь", "Периферия", "Оптическая мышь USB", 1490, 25),
            ("Механическая клавиатура", "Периферия", "Компактная клавиатура", 5990, 12),
            ("Монитор 24 дюйма", "Мониторы", "Full HD IPS", 12990, 8),
            ("USB-C кабель", "Аксессуары", "Кабель 1 метр", 490, 50),
            ("Веб-камера", "Периферия", "Full HD", 3490, 15),
            ("SSD 1 ТБ", "Комплектующие", "NVMe накопитель", 8990, 10),
            ("Наушники", "Аксессуары", "Проводные", 2790, 20),
            ("Видеокарта", "Комплектующие", "Игровая видеокарта", 45990, 4),
        ]
        pd.DataFrame(data, columns=["name", "category", "description", "price", "stock"]).to_excel(SAMPLE_FILE, index=False)
    return SAMPLE_FILE

def read_products(path):
    frame = pd.read_excel(path)
    required = {"name", "category", "description", "price", "stock"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Нет обязательных столбцов: {', '.join(sorted(missing))}")
    frame = frame.dropna(subset=["name", "category", "price"]).copy()
    frame["name"] = frame["name"].astype(str).str.strip()
    frame["category"] = frame["category"].astype(str).str.strip()
    frame["description"] = frame["description"].fillna("").astype(str)
    frame["price"] = pd.to_numeric(frame["price"], errors="coerce")
    frame["stock"] = pd.to_numeric(frame["stock"], errors="coerce").fillna(0)
    frame = frame.dropna(subset=["price"])
    frame = frame[(frame.name != "") & (frame.category != "") & (frame.price >= 0) & (frame.stock >= 0)]
    frame["stock"] = frame["stock"].astype(int)
    return frame.drop_duplicates(subset=["name"], keep="last")
