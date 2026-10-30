import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


class QwerSql:
    """Работа с каталогом спортивной одежды и учётной записью клиента."""

    PAGE_SIZE = 4

    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "sportswear_shop"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
        )
        self.cur = self.conn.cursor()

    def close(self):
        if getattr(self, "cur", None):
            self.cur.close()
        if getattr(self, "conn", None):
            self.conn.close()

    def count_products(self):
        self.cur.execute("SELECT COUNT(*) FROM v_products_full;")
        return self.cur.fetchone()[0]

    def total_pages(self):
        total = self.count_products()
        return max(1, (total + self.PAGE_SIZE - 1) // self.PAGE_SIZE)

    def show_products(self, page=0):
        offset = self.PAGE_SIZE * max(0, page)
        self.cur.execute(
            """SELECT id, name, category, product_type, brand, material,
                      size, color, quantity, price, discount, image_path
               FROM v_products_full
               ORDER BY id LIMIT %s OFFSET %s;""",
            (self.PAGE_SIZE, offset),
        )
        return self.cur.fetchall()

    def get_auth(self, login, passw):
        self.cur.execute(
            """SELECT id, COALESCE(NULLIF(fname, ''), login)
               FROM client WHERE login = %s AND password = %s LIMIT 1;""",
            (login, passw),
        )
        row = self.cur.fetchone()
        return {"id": row[0], "name": row[1]} if row else None

    def get_user_info(self, user_id):
        self.cur.execute(
            "SELECT fname, lname, email, phone FROM client WHERE id = %s",
            (user_id,),
        )
        row = self.cur.fetchone()
        if not row:
            return None
        return {
            "fname": row[0] or "", "lname": row[1] or "",
            "email": row[2] or "", "phone": row[3] or "", "id": user_id,
        }

    def set_new_user_data(self, fname, lname, email, phone, user_id):
        self.cur.execute(
            """UPDATE client SET fname=%s, lname=%s, email=NULLIF(%s, ''),
                      phone=NULLIF(%s, '') WHERE id=%s""",
            (fname, lname, email, phone, user_id),
        )
        self.conn.commit()

    def update_password(self, user_id, new_password):
        self.cur.execute(
            "UPDATE client SET password=%s WHERE id=%s",
            (new_password, user_id),
        )
        self.conn.commit()

    def verify_password(self, user_id, password):
        self.cur.execute(
            "SELECT 1 FROM client WHERE id=%s AND password=%s",
            (user_id, password),
        )
        return self.cur.fetchone() is not None
