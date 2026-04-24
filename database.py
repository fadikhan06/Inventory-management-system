import sqlite3
import os
import hashlib
import hmac
import base64
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path


class DatabaseManager:
    def __init__(self, db_path: str = "inventory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _initialize(self):
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('admin', 'staff')),
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS shops (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    location TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shop_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    UNIQUE(shop_id, name),
                    FOREIGN KEY(shop_id) REFERENCES shops(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shop_id INTEGER NOT NULL,
                    category_id INTEGER,
                    name TEXT NOT NULL,
                    barcode TEXT,
                    sku TEXT,
                    purchase_price REAL NOT NULL DEFAULT 0,
                    selling_price REAL NOT NULL,
                    quantity INTEGER NOT NULL DEFAULT 0,
                    low_stock_threshold INTEGER NOT NULL DEFAULT 5,
                    updated_at TEXT NOT NULL,
                    UNIQUE(shop_id, barcode),
                    UNIQUE(shop_id, sku),
                    FOREIGN KEY(shop_id) REFERENCES shops(id) ON DELETE CASCADE,
                    FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shop_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    total_amount REAL NOT NULL,
                    total_profit REAL NOT NULL,
                    sold_at TEXT NOT NULL,
                    FOREIGN KEY(shop_id) REFERENCES shops(id) ON DELETE CASCADE,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS sale_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price REAL NOT NULL,
                    unit_cost REAL NOT NULL,
                    line_total REAL NOT NULL,
                    line_profit REAL NOT NULL,
                    FOREIGN KEY(sale_id) REFERENCES sales(id) ON DELETE CASCADE,
                    FOREIGN KEY(product_id) REFERENCES products(id)
                );
                """
            )

            admin_exists = conn.execute("SELECT id FROM users WHERE username = ?", ("admin",)).fetchone()
            if not admin_exists:
                conn.execute(
                    "INSERT INTO users(username, password, role, created_at) VALUES(?,?,?,?)",
                    ("admin", self._hash_password("admin123"), "admin", datetime.now(timezone.utc).isoformat()),
                )

            shop_exists = conn.execute("SELECT id FROM shops LIMIT 1").fetchone()
            if not shop_exists:
                conn.execute(
                    "INSERT INTO shops(name, location, created_at) VALUES(?,?,?)",
                    ("Main Shop", "HQ", datetime.now(timezone.utc).isoformat()),
                )

    def execute(self, query, params=()):
        with self.connect() as conn:
            return conn.execute(query, params)

    def fetchall(self, query, params=()):
        with self.connect() as conn:
            return conn.execute(query, params).fetchall()

    def fetchone(self, query, params=()):
        with self.connect() as conn:
            return conn.execute(query, params).fetchone()

    def get_shops(self):
        return self.fetchall("SELECT * FROM shops ORDER BY name")

    def upsert_shop(self, name: str, location: str = ""):
        with self.connect() as conn:
            existing = conn.execute("SELECT id FROM shops WHERE name=?", (name.strip(),)).fetchone()
            if existing:
                conn.execute("UPDATE shops SET location=? WHERE id=?", (location.strip(), existing["id"]))
                return existing["id"]
            cur = conn.execute(
                "INSERT INTO shops(name, location, created_at) VALUES(?,?,?)",
                (name.strip(), location.strip(), datetime.now(timezone.utc).isoformat()),
            )
            return cur.lastrowid

    @staticmethod
    def _hash_password(password: str, salt: bytes | None = None) -> str:
        salt = salt or os.urandom(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200000)
        return f"pbkdf2_sha256${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"

    @staticmethod
    def _verify_password(stored_password: str, provided_password: str) -> bool:
        if not stored_password:
            return False
        if stored_password.startswith("pbkdf2_sha256$"):
            try:
                _, salt_b64, digest_b64 = stored_password.split("$", 2)
                salt = base64.b64decode(salt_b64.encode())
                expected = base64.b64decode(digest_b64.encode())
                actual = hashlib.pbkdf2_hmac("sha256", provided_password.encode("utf-8"), salt, 200000)
                return hmac.compare_digest(actual, expected)
            except Exception:
                return False
        return hmac.compare_digest(stored_password, provided_password)

    def get_user(self, username: str, password: str):
        user = self.fetchone("SELECT * FROM users WHERE username=?", (username.strip(),))
        if not user:
            return None
        if self._verify_password(user["password"], password):
            if not str(user["password"]).startswith("pbkdf2_sha256$"):
                with self.connect() as conn:
                    conn.execute(
                        "UPDATE users SET password=? WHERE id=?",
                        (self._hash_password(password), user["id"]),
                    )
                user = self.fetchone("SELECT * FROM users WHERE id=?", (user["id"],))
            return user
        return None

    def create_user(self, username: str, password: str, role: str):
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO users(username, password, role, created_at) VALUES(?,?,?,?)",
                (username.strip(), self._hash_password(password), role, datetime.now(timezone.utc).isoformat()),
            )

    def get_categories(self, shop_id: int):
        return self.fetchall(
            "SELECT id, name, description FROM categories WHERE shop_id=? ORDER BY name",
            (shop_id,),
        )

    def add_category(self, shop_id: int, name: str, description: str):
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO categories(shop_id, name, description) VALUES(?,?,?)",
                (shop_id, name.strip(), description.strip()),
            )

    def delete_category(self, category_id: int):
        with self.connect() as conn:
            conn.execute("DELETE FROM categories WHERE id=?", (category_id,))

    def add_product(self, shop_id, category_id, name, barcode, sku, purchase_price, selling_price, quantity, low_stock_threshold):
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO products(shop_id, category_id, name, barcode, sku, purchase_price, selling_price, quantity, low_stock_threshold, updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    shop_id,
                    category_id or None,
                    name.strip(),
                    (barcode or "").strip() or None,
                    (sku or "").strip() or None,
                    float(purchase_price),
                    float(selling_price),
                    int(quantity),
                    int(low_stock_threshold),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

    def update_product(self, product_id, category_id, name, barcode, sku, purchase_price, selling_price, quantity, low_stock_threshold):
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE products
                SET category_id=?, name=?, barcode=?, sku=?, purchase_price=?, selling_price=?, quantity=?, low_stock_threshold=?, updated_at=?
                WHERE id=?
                """,
                (
                    category_id or None,
                    name.strip(),
                    (barcode or "").strip() or None,
                    (sku or "").strip() or None,
                    float(purchase_price),
                    float(selling_price),
                    int(quantity),
                    int(low_stock_threshold),
                    datetime.now(timezone.utc).isoformat(),
                    product_id,
                ),
            )

    def delete_product(self, product_id):
        with self.connect() as conn:
            conn.execute("DELETE FROM products WHERE id=?", (product_id,))

    def get_products(self, shop_id: int, query: str = ""):
        q = (query or "").strip().lower()
        if q:
            return self.fetchall(
                """
                SELECT p.*, c.name as category_name
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.shop_id=?
                  AND (
                      lower(p.name) LIKE ? OR lower(IFNULL(p.barcode,'')) LIKE ? OR lower(IFNULL(p.sku,'')) LIKE ?
                  )
                ORDER BY p.name
                """,
                (shop_id, f"%{q}%", f"%{q}%", f"%{q}%"),
            )
        return self.fetchall(
            """
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.shop_id=?
            ORDER BY p.name
            """,
            (shop_id,),
        )

    def get_product_by_id(self, product_id: int):
        return self.fetchone("SELECT * FROM products WHERE id=?", (product_id,))

    def get_product_by_barcode(self, shop_id: int, barcode: str):
        return self.fetchone(
            "SELECT * FROM products WHERE shop_id=? AND barcode=?",
            (shop_id, barcode.strip()),
        )

    def get_products_map(self, product_ids: list[int]):
        if not product_ids:
            return {}
        sanitized_ids = []
        for pid in product_ids:
            try:
                sanitized_ids.append(int(pid))
            except (TypeError, ValueError) as exc:
                raise ValueError("Product IDs must be integers") from exc
        placeholders = ",".join("?" for _ in sanitized_ids)
        rows = self.fetchall(f"SELECT * FROM products WHERE id IN ({placeholders})", tuple(sanitized_ids))
        return {row["id"]: row for row in rows}

    def get_low_stock_products(self, shop_id: int):
        return self.fetchall(
            "SELECT * FROM products WHERE shop_id=? AND quantity <= low_stock_threshold ORDER BY quantity ASC",
            (shop_id,),
        )

    def create_sale(self, shop_id: int, user_id: int, cart_items: list[dict]):
        if not cart_items:
            raise ValueError("Cart is empty")

        sold_at = datetime.now(timezone.utc).isoformat()
        with self.connect() as conn:
            total_amount = 0.0
            total_profit = 0.0
            validated_products = {}

            for item in cart_items:
                product = conn.execute("SELECT * FROM products WHERE id=?", (item["product_id"],)).fetchone()
                if not product:
                    raise ValueError(f"Product ID {item['product_id']} not found")
                if product["quantity"] < item["quantity"]:
                    raise ValueError(f"Insufficient stock for {product['name']}")
                validated_products[item["product_id"]] = product

                line_total = float(product["selling_price"]) * int(item["quantity"])
                line_profit = (float(product["selling_price"]) - float(product["purchase_price"])) * int(item["quantity"])
                total_amount += line_total
                total_profit += line_profit

            sale_cur = conn.execute(
                "INSERT INTO sales(shop_id, user_id, total_amount, total_profit, sold_at) VALUES(?,?,?,?,?)",
                (shop_id, user_id, total_amount, total_profit, sold_at),
            )
            sale_id = sale_cur.lastrowid

            for item in cart_items:
                product = validated_products[item["product_id"]]
                qty = int(item["quantity"])
                unit_price = float(product["selling_price"])
                unit_cost = float(product["purchase_price"])
                line_total = unit_price * qty
                line_profit = (unit_price - unit_cost) * qty

                conn.execute(
                    """
                    INSERT INTO sale_items(sale_id, product_id, quantity, unit_price, unit_cost, line_total, line_profit)
                    VALUES(?,?,?,?,?,?,?)
                    """,
                    (sale_id, product["id"], qty, unit_price, unit_cost, line_total, line_profit),
                )

                conn.execute(
                    "UPDATE products SET quantity = quantity - ?, updated_at=? WHERE id=?",
                    (qty, datetime.now(timezone.utc).isoformat(), product["id"]),
                )

            return sale_id

    def get_sale(self, sale_id: int):
        sale = self.fetchone(
            """
            SELECT s.*, u.username, sh.name as shop_name
            FROM sales s
            JOIN users u ON s.user_id = u.id
            JOIN shops sh ON s.shop_id = sh.id
            WHERE s.id=?
            """,
            (sale_id,),
        )
        items = self.fetchall(
            """
            SELECT si.*, p.name as product_name
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            WHERE si.sale_id=?
            """,
            (sale_id,),
        )
        return sale, items

    def get_sales_history(self, shop_id: int):
        return self.fetchall(
            """
            SELECT s.id, s.total_amount, s.total_profit, s.sold_at, u.username
            FROM sales s
            JOIN users u ON s.user_id = u.id
            WHERE s.shop_id=?
            ORDER BY s.sold_at DESC
            """,
            (shop_id,),
        )

    def _sales_between(self, shop_id: int, start: datetime, end: datetime):
        return self.fetchall(
            """
            SELECT id, total_amount, total_profit, sold_at
            FROM sales
            WHERE shop_id=? AND sold_at >= ? AND sold_at < ?
            ORDER BY sold_at DESC
            """,
            (shop_id, start.isoformat(), end.isoformat()),
        )

    def get_sales_report(self, shop_id: int, period: str):
        now = datetime.now(timezone.utc)
        if period == "daily":
            start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
            end = start + timedelta(days=1)
        elif period == "weekly":
            start = now - timedelta(days=7)
            end = now
        elif period == "monthly":
            start = now - timedelta(days=30)
            end = now
        else:
            raise ValueError("Invalid period")
        sales = self._sales_between(shop_id, start, end)
        revenue = sum(float(r["total_amount"]) for r in sales)
        profit = sum(float(r["total_profit"]) for r in sales)
        return {
            "period": period,
            "start": start,
            "end": end,
            "count": len(sales),
            "revenue": revenue,
            "profit": profit,
            "sales": sales,
        }

    def get_dashboard_metrics(self, shop_id: int):
        products = self.fetchone("SELECT COUNT(*) as c FROM products WHERE shop_id=?", (shop_id,))["c"]
        stock_units = self.fetchone("SELECT COALESCE(SUM(quantity), 0) as q FROM products WHERE shop_id=?", (shop_id,))["q"]
        sales_today = self.get_sales_report(shop_id, "daily")
        return {
            "product_count": products,
            "stock_units": stock_units,
            "sales_count_today": sales_today["count"],
            "revenue_today": sales_today["revenue"],
            "profit_today": sales_today["profit"],
        }
