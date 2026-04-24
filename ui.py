import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

from database import DatabaseManager
from services import ExportService, ReceiptService, BackupService


class InventoryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Inventory Management System")
        self.geometry("1280x760")
        self.minsize(1100, 700)

        self.base_dir = Path(__file__).resolve().parent
        self.db = DatabaseManager(str(self.base_dir / "inventory.db"))
        self.user = None
        self.shop_id = None
        self.dark_mode = False

        self.theme = {
            "bg": "#F4F7FA",
            "panel": "#FFFFFF",
            "fg": "#212529",
            "accent": "#0D6EFD",
        }

        self._build_login()

    def _apply_theme(self):
        bg = self.theme["bg"]
        self.configure(bg=bg)
        if hasattr(self, "container"):
            self.container.configure(bg=bg)
        if hasattr(self, "sidebar"):
            self.sidebar.configure(bg=self.theme["panel"])

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            self.theme = {"bg": "#1F2937", "panel": "#111827", "fg": "#E5E7EB", "accent": "#60A5FA"}
        else:
            self.theme = {"bg": "#F4F7FA", "panel": "#FFFFFF", "fg": "#212529", "accent": "#0D6EFD"}
        self._apply_theme()

    def notify(self, text: str):
        self.status_var.set(text)

    def _build_login(self):
        for w in self.winfo_children():
            w.destroy()

        frame = tk.Frame(self, bg=self.theme["bg"])
        frame.pack(fill="both", expand=True)

        card = tk.Frame(frame, bg=self.theme["panel"], padx=30, pady=30)
        card.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(card, text="Inventory Management", bg=self.theme["panel"], fg=self.theme["fg"], font=("Segoe UI", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 20))
        tk.Label(card, text="Username", bg=self.theme["panel"], fg=self.theme["fg"]).grid(row=1, column=0, sticky="w")
        tk.Label(card, text="Password", bg=self.theme["panel"], fg=self.theme["fg"]).grid(row=2, column=0, sticky="w", pady=(8, 0))

        self.username_entry = ttk.Entry(card, width=28)
        self.password_entry = ttk.Entry(card, width=28, show="*")
        self.username_entry.grid(row=1, column=1, pady=4)
        self.password_entry.grid(row=2, column=1, pady=8)

        tk.Label(card, text="Shop", bg=self.theme["panel"], fg=self.theme["fg"]).grid(row=3, column=0, sticky="w")
        shops = self.db.get_shops()
        self.shop_map = {s["name"]: s["id"] for s in shops}
        self.shop_combo = ttk.Combobox(card, values=list(self.shop_map.keys()), state="readonly", width=25)
        if shops:
            self.shop_combo.set(shops[0]["name"])
        self.shop_combo.grid(row=3, column=1, pady=8)

        ttk.Button(card, text="Login", command=self.login).grid(row=4, column=0, columnspan=2, sticky="ew", pady=(12, 4))

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        shop_name = self.shop_combo.get().strip()
        if not username or not password:
            messagebox.showwarning("Validation", "Username and password are required")
            return
        user = self.db.get_user(username, password)
        if not user:
            messagebox.showerror("Login Failed", "Invalid credentials")
            return
        self.user = user
        self.shop_id = self.shop_map.get(shop_name)
        if not self.shop_id:
            messagebox.showerror("Error", "Please select a valid shop")
            return
        self._build_main_ui()

    def _build_main_ui(self):
        for w in self.winfo_children():
            w.destroy()

        self.container = tk.Frame(self, bg=self.theme["bg"])
        self.container.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(self.container, bg=self.theme["panel"], width=220)
        self.sidebar.pack(side="left", fill="y")

        content = tk.Frame(self.container, bg=self.theme["bg"])
        content.pack(side="right", fill="both", expand=True)

        tk.Label(self.sidebar, text="IMS", bg=self.theme["panel"], fg=self.theme["accent"], font=("Segoe UI", 18, "bold")).pack(pady=16)
        tk.Label(self.sidebar, text=f"{self.user['username']} ({self.user['role']})", bg=self.theme["panel"], fg=self.theme["fg"]).pack(pady=(0, 10))

        self.status_var = tk.StringVar(value="Ready")

        self.notebook = ttk.Notebook(content)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.dashboard_tab = tk.Frame(self.notebook, bg=self.theme["bg"])
        self.product_tab = tk.Frame(self.notebook, bg=self.theme["bg"])
        self.category_tab = tk.Frame(self.notebook, bg=self.theme["bg"])
        self.sales_tab = tk.Frame(self.notebook, bg=self.theme["bg"])
        self.history_tab = tk.Frame(self.notebook, bg=self.theme["bg"])
        self.reports_tab = tk.Frame(self.notebook, bg=self.theme["bg"])

        self.notebook.add(self.dashboard_tab, text="Dashboard")
        self.notebook.add(self.product_tab, text="Products")
        self.notebook.add(self.category_tab, text="Categories")
        self.notebook.add(self.sales_tab, text="Sales")
        self.notebook.add(self.history_tab, text="History")
        self.notebook.add(self.reports_tab, text="Reports")

        ttk.Button(self.sidebar, text="Dashboard", command=lambda: self.notebook.select(self.dashboard_tab)).pack(fill="x", padx=10, pady=3)
        ttk.Button(self.sidebar, text="Products", command=lambda: self.notebook.select(self.product_tab)).pack(fill="x", padx=10, pady=3)
        ttk.Button(self.sidebar, text="Categories", command=lambda: self.notebook.select(self.category_tab)).pack(fill="x", padx=10, pady=3)
        ttk.Button(self.sidebar, text="Sales", command=lambda: self.notebook.select(self.sales_tab)).pack(fill="x", padx=10, pady=3)
        ttk.Button(self.sidebar, text="Reports", command=lambda: self.notebook.select(self.reports_tab)).pack(fill="x", padx=10, pady=3)
        ttk.Button(self.sidebar, text="Dark Mode", command=self.toggle_theme).pack(fill="x", padx=10, pady=(12, 3))
        ttk.Button(self.sidebar, text="Backup", command=self.backup_db).pack(fill="x", padx=10, pady=3)
        ttk.Button(self.sidebar, text="Restore", command=self.restore_db).pack(fill="x", padx=10, pady=3)
        ttk.Button(self.sidebar, text="Logout", command=self._build_login).pack(fill="x", padx=10, pady=(20, 3))

        status = tk.Label(content, textvariable=self.status_var, anchor="w", bg=self.theme["panel"], fg=self.theme["fg"])
        status.pack(fill="x", padx=10, pady=(0, 10))

        self._build_dashboard_tab()
        self._build_category_tab()
        self._build_product_tab()
        self._build_sales_tab()
        self._build_history_tab()
        self._build_reports_tab()
        self.refresh_all()
        self._apply_role_permissions()

    def _apply_role_permissions(self):
        if self.user["role"] == "staff":
            self.notebook.tab(self.category_tab, state="disabled")

    def _build_dashboard_tab(self):
        self.metrics_text = tk.Text(self.dashboard_tab, height=8, state="disabled")
        self.metrics_text.pack(fill="x", padx=12, pady=12)

        tk.Label(self.dashboard_tab, text="Low Stock Alerts", bg=self.theme["bg"], fg=self.theme["fg"], font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=12)
        self.low_stock_tree = ttk.Treeview(self.dashboard_tab, columns=("id", "name", "qty", "threshold"), show="headings", height=12)
        for c, t in [("id", "ID"), ("name", "Product"), ("qty", "Stock"), ("threshold", "Threshold")]:
            self.low_stock_tree.heading(c, text=t)
        self.low_stock_tree.pack(fill="both", expand=True, padx=12, pady=8)

    def _build_category_tab(self):
        top = tk.Frame(self.category_tab, bg=self.theme["bg"])
        top.pack(fill="x", padx=12, pady=10)

        tk.Label(top, text="Name", bg=self.theme["bg"], fg=self.theme["fg"]).grid(row=0, column=0, sticky="w")
        tk.Label(top, text="Description", bg=self.theme["bg"], fg=self.theme["fg"]).grid(row=1, column=0, sticky="w")

        self.category_name = ttk.Entry(top, width=35)
        self.category_desc = ttk.Entry(top, width=35)
        self.category_name.grid(row=0, column=1, padx=5, pady=4)
        self.category_desc.grid(row=1, column=1, padx=5, pady=4)

        ttk.Button(top, text="Add Category", command=self.add_category).grid(row=0, column=2, padx=8)
        ttk.Button(top, text="Delete Selected", command=self.delete_category).grid(row=1, column=2, padx=8)

        self.category_tree = ttk.Treeview(self.category_tab, columns=("id", "name", "description"), show="headings", height=16)
        for c in ("id", "name", "description"):
            self.category_tree.heading(c, text=c.title())
        self.category_tree.pack(fill="both", expand=True, padx=12, pady=8)

    def _build_product_tab(self):
        form = tk.Frame(self.product_tab, bg=self.theme["bg"])
        form.pack(fill="x", padx=12, pady=10)

        labels = ["Name", "Category", "Barcode", "SKU", "Purchase Price", "Selling Price", "Quantity", "Low Stock"]
        for i, label in enumerate(labels):
            tk.Label(form, text=label, bg=self.theme["bg"], fg=self.theme["fg"]).grid(row=i // 4, column=(i % 4) * 2, sticky="w", padx=4, pady=3)

        self.prod_name = ttk.Entry(form, width=18)
        self.prod_category = ttk.Combobox(form, state="readonly", width=16)
        self.prod_barcode = ttk.Entry(form, width=18)
        self.prod_sku = ttk.Entry(form, width=18)
        self.prod_purchase = ttk.Entry(form, width=18)
        self.prod_selling = ttk.Entry(form, width=18)
        self.prod_qty = ttk.Entry(form, width=18)
        self.prod_low = ttk.Entry(form, width=18)

        entries = [self.prod_name, self.prod_category, self.prod_barcode, self.prod_sku, self.prod_purchase, self.prod_selling, self.prod_qty, self.prod_low]
        for i, widget in enumerate(entries):
            widget.grid(row=i // 4, column=(i % 4) * 2 + 1, padx=4, pady=3)

        btns = tk.Frame(form, bg=self.theme["bg"])
        btns.grid(row=3, column=0, columnspan=8, sticky="w", pady=8)
        ttk.Button(btns, text="Add", command=self.add_product).pack(side="left", padx=4)
        ttk.Button(btns, text="Update Selected", command=self.update_product).pack(side="left", padx=4)
        ttk.Button(btns, text="Delete Selected", command=self.delete_product).pack(side="left", padx=4)

        search_bar = tk.Frame(self.product_tab, bg=self.theme["bg"])
        search_bar.pack(fill="x", padx=12)
        tk.Label(search_bar, text="Search", bg=self.theme["bg"], fg=self.theme["fg"]).pack(side="left")
        self.product_search = ttk.Entry(search_bar, width=35)
        self.product_search.pack(side="left", padx=5)
        ttk.Button(search_bar, text="Find", command=self.refresh_products).pack(side="left")

        cols = ("id", "name", "category", "barcode", "sku", "purchase", "selling", "qty", "low")
        self.product_tree = ttk.Treeview(self.product_tab, columns=cols, show="headings", height=14)
        for c in cols:
            self.product_tree.heading(c, text=c.title())
        self.product_tree.pack(fill="both", expand=True, padx=12, pady=8)

    def _build_sales_tab(self):
        self.cart_items = []
        top = tk.Frame(self.sales_tab, bg=self.theme["bg"])
        top.pack(fill="x", padx=12, pady=10)

        tk.Label(top, text="Barcode", bg=self.theme["bg"], fg=self.theme["fg"]).grid(row=0, column=0, sticky="w")
        self.sale_barcode = ttk.Entry(top, width=20)
        self.sale_barcode.grid(row=0, column=1, padx=5)
        ttk.Button(top, text="Find", command=self.add_by_barcode).grid(row=0, column=2, padx=5)

        tk.Label(top, text="Product", bg=self.theme["bg"], fg=self.theme["fg"]).grid(row=1, column=0, sticky="w", pady=6)
        self.sale_product = ttk.Combobox(top, state="readonly", width=28)
        self.sale_product.grid(row=1, column=1, padx=5)

        tk.Label(top, text="Quantity", bg=self.theme["bg"], fg=self.theme["fg"]).grid(row=1, column=2, sticky="w")
        self.sale_qty = ttk.Entry(top, width=10)
        self.sale_qty.grid(row=1, column=3, padx=5)
        self.sale_qty.insert(0, "1")

        ttk.Button(top, text="Add to Cart", command=self.add_to_cart).grid(row=1, column=4, padx=6)
        ttk.Button(top, text="Complete Sale", command=self.complete_sale).grid(row=1, column=5, padx=6)

        self.cart_tree = ttk.Treeview(self.sales_tab, columns=("id", "name", "qty", "price", "line"), show="headings", height=15)
        for c in ("id", "name", "qty", "price", "line"):
            self.cart_tree.heading(c, text=c.title())
        self.cart_tree.pack(fill="both", expand=True, padx=12, pady=8)

        self.cart_total_var = tk.StringVar(value="Cart Total: 0.00")
        tk.Label(self.sales_tab, textvariable=self.cart_total_var, bg=self.theme["bg"], fg=self.theme["fg"], font=("Segoe UI", 11, "bold")).pack(anchor="e", padx=18, pady=(0, 8))

    def _build_history_tab(self):
        self.history_tree = ttk.Treeview(self.history_tab, columns=("id", "total", "profit", "date", "user"), show="headings", height=20)
        for c in ("id", "total", "profit", "date", "user"):
            self.history_tree.heading(c, text=c.title())
        self.history_tree.pack(fill="both", expand=True, padx=12, pady=12)

    def _build_reports_tab(self):
        frame = tk.Frame(self.reports_tab, bg=self.theme["bg"])
        frame.pack(fill="x", padx=12, pady=12)

        tk.Label(frame, text="Period", bg=self.theme["bg"], fg=self.theme["fg"]).grid(row=0, column=0, sticky="w")
        self.report_period = ttk.Combobox(frame, values=["daily", "weekly", "monthly"], state="readonly", width=12)
        self.report_period.set("daily")
        self.report_period.grid(row=0, column=1, padx=5)

        ttk.Button(frame, text="Generate", command=self.generate_report).grid(row=0, column=2, padx=5)
        ttk.Button(frame, text="Export CSV", command=self.export_report_csv).grid(row=0, column=3, padx=5)
        ttk.Button(frame, text="Export PDF", command=self.export_report_pdf).grid(row=0, column=4, padx=5)

        self.report_text = tk.Text(self.reports_tab, height=28)
        self.report_text.pack(fill="both", expand=True, padx=12, pady=8)
        self.current_report = None

    def refresh_all(self):
        self.refresh_dashboard()
        self.refresh_categories()
        self.refresh_products()
        self.refresh_sales_dropdown()
        self.refresh_history()

    def refresh_dashboard(self):
        metrics = self.db.get_dashboard_metrics(self.shop_id)
        text = (
            f"Total Products: {metrics['product_count']}\n"
            f"Total Stock Units: {metrics['stock_units']}\n"
            f"Today's Sales Count: {metrics['sales_count_today']}\n"
            f"Today's Revenue: {metrics['revenue_today']:.2f}\n"
            f"Today's Profit: {metrics['profit_today']:.2f}\n"
        )
        self.metrics_text.config(state="normal")
        self.metrics_text.delete("1.0", "end")
        self.metrics_text.insert("1.0", text)
        self.metrics_text.config(state="disabled")

        for i in self.low_stock_tree.get_children():
            self.low_stock_tree.delete(i)
        low_stock = self.db.get_low_stock_products(self.shop_id)
        for row in low_stock:
            self.low_stock_tree.insert("", "end", values=(row["id"], row["name"], row["quantity"], row["low_stock_threshold"]))
        if low_stock:
            self.notify(f"Low stock alert: {len(low_stock)} product(s) need restock")

    def refresh_categories(self):
        categories = self.db.get_categories(self.shop_id)
        for i in self.category_tree.get_children():
            self.category_tree.delete(i)
        for c in categories:
            self.category_tree.insert("", "end", values=(c["id"], c["name"], c["description"] or ""))

        names = [c["name"] for c in categories]
        self.prod_category["values"] = names
        self.category_id_by_name = {c["name"]: c["id"] for c in categories}

    def refresh_products(self):
        query = self.product_search.get().strip() if hasattr(self, "product_search") else ""
        products = self.db.get_products(self.shop_id, query)
        for i in self.product_tree.get_children():
            self.product_tree.delete(i)
        for p in products:
            self.product_tree.insert(
                "",
                "end",
                values=(p["id"], p["name"], p["category_name"] or "", p["barcode"] or "", p["sku"] or "", p["purchase_price"], p["selling_price"], p["quantity"], p["low_stock_threshold"]),
            )

    def refresh_sales_dropdown(self):
        products = self.db.get_products(self.shop_id)
        self.sale_product_map = {f"{p['name']} (ID:{p['id']})": p["id"] for p in products}
        self.sale_product["values"] = list(self.sale_product_map.keys())

    def refresh_history(self):
        sales = self.db.get_sales_history(self.shop_id)
        for i in self.history_tree.get_children():
            self.history_tree.delete(i)
        for s in sales:
            self.history_tree.insert("", "end", values=(s["id"], f"{s['total_amount']:.2f}", f"{s['total_profit']:.2f}", s["sold_at"], s["username"]))

    def _selected_category_id(self):
        cat_name = self.prod_category.get().strip()
        if not cat_name:
            return None
        return self.category_id_by_name.get(cat_name)

    def add_category(self):
        if self.user["role"] != "admin":
            messagebox.showwarning("Permission", "Only admin can manage categories")
            return
        name = self.category_name.get().strip()
        desc = self.category_desc.get().strip()
        if not name:
            messagebox.showwarning("Validation", "Category name is required")
            return
        try:
            self.db.add_category(self.shop_id, name, desc)
            self.notify("Category added")
            self.category_name.delete(0, "end")
            self.category_desc.delete(0, "end")
            self.refresh_categories()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_category(self):
        if self.user["role"] != "admin":
            messagebox.showwarning("Permission", "Only admin can manage categories")
            return
        selected = self.category_tree.selection()
        if not selected:
            return
        item = self.category_tree.item(selected[0])["values"]
        try:
            self.db.delete_category(int(item[0]))
            self.notify("Category deleted")
            self.refresh_categories()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _validate_product_inputs(self):
        try:
            name = self.prod_name.get().strip()
            if not name:
                raise ValueError("Product name is required")
            purchase = float(self.prod_purchase.get())
            selling = float(self.prod_selling.get())
            qty = int(self.prod_qty.get())
            low = int(self.prod_low.get())
            if purchase < 0 or selling < 0 or qty < 0 or low < 0:
                raise ValueError("Numeric values must be non-negative")
            return {
                "name": name,
                "category_id": self._selected_category_id(),
                "barcode": self.prod_barcode.get().strip(),
                "sku": self.prod_sku.get().strip(),
                "purchase": purchase,
                "selling": selling,
                "qty": qty,
                "low": low,
            }
        except ValueError as e:
            raise ValueError(str(e)) from e

    def add_product(self):
        if self.user["role"] != "admin":
            messagebox.showwarning("Permission", "Only admin can add/update/delete products")
            return
        try:
            p = self._validate_product_inputs()
            self.db.add_product(self.shop_id, p["category_id"], p["name"], p["barcode"], p["sku"], p["purchase"], p["selling"], p["qty"], p["low"])
            self.notify("Product added")
            self.refresh_all()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_product(self):
        if self.user["role"] != "admin":
            messagebox.showwarning("Permission", "Only admin can add/update/delete products")
            return
        selected = self.product_tree.selection()
        if not selected:
            messagebox.showwarning("Selection", "Select a product to update")
            return
        try:
            p = self._validate_product_inputs()
            product_id = int(self.product_tree.item(selected[0])["values"][0])
            self.db.update_product(product_id, p["category_id"], p["name"], p["barcode"], p["sku"], p["purchase"], p["selling"], p["qty"], p["low"])
            self.notify("Product updated")
            self.refresh_all()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_product(self):
        if self.user["role"] != "admin":
            messagebox.showwarning("Permission", "Only admin can add/update/delete products")
            return
        selected = self.product_tree.selection()
        if not selected:
            return
        product_id = int(self.product_tree.item(selected[0])["values"][0])
        try:
            self.db.delete_product(product_id)
            self.notify("Product deleted")
            self.refresh_all()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def add_by_barcode(self):
        barcode = self.sale_barcode.get().strip()
        if not barcode:
            messagebox.showwarning("Validation", "Enter barcode")
            return
        product = self.db.get_product_by_barcode(self.shop_id, barcode)
        if not product:
            messagebox.showerror("Not found", "Barcode not found")
            return
        self._add_item_to_cart(product["id"], 1)

    def add_to_cart(self):
        product_label = self.sale_product.get().strip()
        if not product_label:
            messagebox.showwarning("Validation", "Select a product")
            return
        try:
            qty = int(self.sale_qty.get())
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Validation", "Quantity must be a positive integer")
            return
        product_id = self.sale_product_map.get(product_label)
        self._add_item_to_cart(product_id, qty)

    def _add_item_to_cart(self, product_id, qty):
        product = self.db.get_product_by_id(product_id)
        if not product:
            messagebox.showerror("Error", "Product not found")
            return
        if product["quantity"] < qty:
            messagebox.showwarning("Stock", f"Insufficient stock. Available: {product['quantity']}")
            return

        for c in self.cart_items:
            if c["product_id"] == product_id:
                c["quantity"] += qty
                break
        else:
            self.cart_items.append({"product_id": product_id, "quantity": qty})

        self.refresh_cart_view()
        self.notify(f"Added {product['name']} x{qty}")

    def refresh_cart_view(self):
        for i in self.cart_tree.get_children():
            self.cart_tree.delete(i)
        total = 0.0
        products = self.db.get_products_map([c["product_id"] for c in self.cart_items])
        for c in self.cart_items:
            p = products.get(c["product_id"])
            if not p:
                continue
            line = float(p["selling_price"]) * int(c["quantity"])
            total += line
            self.cart_tree.insert("", "end", values=(p["id"], p["name"], c["quantity"], f"{p['selling_price']:.2f}", f"{line:.2f}"))
        self.cart_total_var.set(f"Cart Total: {total:.2f}")

    def complete_sale(self):
        if not self.cart_items:
            messagebox.showwarning("Cart", "Cart is empty")
            return
        try:
            sale_id = self.db.create_sale(self.shop_id, int(self.user["id"]), self.cart_items)
            sale, items = self.db.get_sale(sale_id)
            receipt_file = ReceiptService.create_receipt(sale, items, str(self.base_dir / "receipts"))
            self.notify(f"Sale #{sale_id} complete. Receipt: {receipt_file}")
            self.cart_items = []
            self.refresh_cart_view()
            self.refresh_all()
            messagebox.showinfo("Sale Completed", f"Sale #{sale_id} completed.\nReceipt saved to:\n{receipt_file}")
        except Exception as e:
            messagebox.showerror("Sale Error", str(e))

    def generate_report(self):
        period = self.report_period.get().strip()
        try:
            report = self.db.get_sales_report(self.shop_id, period)
            self.current_report = report
            text = (
                f"Sales Report ({period.title()})\n"
                f"From: {report['start'].isoformat()}\n"
                f"To: {report['end'].isoformat()}\n"
                f"Transactions: {report['count']}\n"
                f"Revenue: {report['revenue']:.2f}\n"
                f"Profit: {report['profit']:.2f}\n"
                + "\nTransactions:\n"
            )
            for s in report["sales"]:
                text += f"- Sale #{s['id']} | Revenue {s['total_amount']:.2f} | Profit {s['total_profit']:.2f} | {s['sold_at']}\n"

            self.report_text.delete("1.0", "end")
            self.report_text.insert("1.0", text)
            self.notify(f"{period.title()} report generated")
        except Exception as e:
            messagebox.showerror("Report Error", str(e))

    def export_report_csv(self):
        if not self.current_report:
            self.generate_report()
        if not self.current_report:
            return
        try:
            file = ExportService.export_report_csv(self.current_report, str(self.base_dir / "exports"))
            self.notify(f"CSV exported: {file}")
            messagebox.showinfo("Export", f"CSV exported to:\n{file}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def export_report_pdf(self):
        if not self.current_report:
            self.generate_report()
        if not self.current_report:
            return
        try:
            file = ExportService.export_report_pdf(self.current_report, str(self.base_dir / "exports"))
            self.notify(f"PDF exported: {file}")
            messagebox.showinfo("Export", f"PDF exported to:\n{file}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def backup_db(self):
        try:
            file = BackupService.backup_database(str(self.base_dir / "inventory.db"), str(self.base_dir / "backups"))
            self.notify(f"Backup created: {file}")
            messagebox.showinfo("Backup", f"Backup saved to:\n{file}")
        except Exception as e:
            messagebox.showerror("Backup Error", str(e))

    def restore_db(self):
        backup_file = filedialog.askopenfilename(title="Select backup file", filetypes=[("Database", "*.db"), ("All files", "*.*")])
        if not backup_file:
            return
        if not messagebox.askyesno("Restore", "Restoring will overwrite current database. Continue?"):
            return
        try:
            BackupService.restore_database(backup_file, str(self.base_dir / "inventory.db"))
            self.notify("Database restored successfully")
            self.refresh_all()
            messagebox.showinfo("Restore", "Database restored successfully")
        except Exception as e:
            messagebox.showerror("Restore Error", str(e))
