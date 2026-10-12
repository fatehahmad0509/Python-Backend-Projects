import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import os


# --- 1. VERİTABANI VE ÜRÜN SINIFI ---
class Product:
    def __init__(self, code, name, price, stock):
        self.code = code
        self.name = name
        self.price = price
        self.stock = stock


def setup_db():
    db = sqlite3.connect("saves.db")
    cursor = db.cursor()
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS inventory
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY,
                       name
                       TEXT,
                       price
                       REAL,
                       stock
                       INTEGER
                   )
                   """)
    cursor.execute("SELECT count(*) FROM inventory")
    if cursor.fetchone()[0] == 0:
        initial_items = [
            (1, "Bread", 1.0, 1000), (2, "Milk (1L)", 2.0, 1000), (3, "Egg (10)", 4.0, 1000),
            (4, "Rice (1KG)", 5.0, 1000), (5, "Pasta", 2.5, 1000), (6, "Gouda Cheese", 7.0, 1000),
            (7, "Stroopwafel", 4.0, 1000), (8, "Organic Milk", 3.0, 1000), (9, "Protein Bar", 3.0, 1000),
            (10, "Water (500ML)", 1.0, 1000), (11, "Fruit Juice", 2.5, 1000), (12, "Coffee", 4.0, 1000),
            (13, "Frozen Pizza", 5.0, 1000), (14, "Sandwich", 3.0, 1000), (15, "Microwave Meal", 7.0, 1000),
            (16, "Detergent", 8.0, 1000), (17, "Toilet Paper", 6.0, 1000), (18, "Shampoo", 7.0, 1000),
            (19, "Cocacola", 4.0, 1000)
        ]
        cursor.executemany("INSERT INTO inventory VALUES (?, ?, ?, ?)", initial_items)
        db.commit()
    db.close()


# --- 2. ANA ARAYÜZ ---
class MarketApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Elite Shop Manager v2.0")
        self.root.geometry("1100x750")
        self.root.configure(bg="#1e1e1e")

        self.db_name = "saves.db"
        self.cart = []
        self.total_price = 0.0
        self.products_list = []

        setup_db()
        self.sync_data()

        # --- TASARIM: SOL PANEL ---
        self.left_panel = tk.Frame(self.root, bg="#252526", width=220)
        self.left_panel.pack(side="left", fill="y")

        tk.Label(self.left_panel, text="SHOP MENU", fg="white", bg="#252526", font=("Arial", 20, "bold")).pack(pady=40)

        tk.Button(self.left_panel, text="Refresh Stocks", bg="#007acc", fg="white", font=("Arial", 10, "bold"),
                  relief="flat", command=self.sync_data).pack(pady=10, padx=20, fill="x")

        tk.Button(self.left_panel, text="Admin Panel", bg="#d71e1e", fg="white", font=("Arial", 10, "bold"),
                  relief="flat", command=self.admin_login).pack(pady=10, padx=20, fill="x")

        self.lbl_total = tk.Label(self.left_panel, text="Total: 0.00 EUR", fg="#4ec9b0", bg="#252526",
                                  font=("Arial", 14, "bold"))
        self.lbl_total.pack(side="bottom", pady=30)

        # --- TASARIM: ORTA PANEL (ÜRÜNLER) ---
        self.mid_panel = tk.Frame(self.root, bg="#1e1e1e")
        self.mid_panel.pack(side="left", fill="both", expand=True, padx=20)

        self.canvas = tk.Canvas(self.mid_panel, bg="#1e1e1e", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.mid_panel, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg="#1e1e1e")

        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # --- TASARIM: SAĞ PANEL (SEPET) ---
        self.right_panel = tk.Frame(self.root, bg="#252526", width=300)
        self.right_panel.pack(side="right", fill="both", padx=10)

        tk.Label(self.right_panel, text="YOUR CART", fg="white", bg="#252526", font=("Arial", 12, "bold")).pack(pady=20)

        self.cart_box = tk.Listbox(self.right_panel, bg="#1e1e1e", fg="white", font=("Arial", 10), borderwidth=0,
                                   selectbackground="#007acc")
        self.cart_box.pack(fill="both", expand=True, padx=10, pady=5)

        tk.Button(self.right_panel, text="Remove Selected", bg="#555555", fg="white", relief="flat",
                  command=self.remove_from_cart).pack(fill="x", padx=10, pady=5)
        tk.Button(self.right_panel, text="COMPLETE PAYMENT", bg="#28a745", fg="white", font=("Arial", 12, "bold"),
                  relief="flat", command=self.complete_payment).pack(fill="x", padx=10, pady=20)

        self.render_products()

    def sync_data(self):
        db = sqlite3.connect(self.db_name)
        cursor = db.cursor()
        cursor.execute("SELECT id, name, price, stock FROM inventory")
        rows = cursor.fetchall()
        self.products_list = [Product(r[0], r[1], r[2], r[3]) for r in rows]
        db.close()
        if hasattr(self, "scroll_frame"): self.render_products()

    def render_products(self):
        for widget in self.scroll_frame.winfo_children(): widget.destroy()
        for item in self.products_list:
            f = tk.Frame(self.scroll_frame, bg="#2d2d2d", pady=8)
            f.pack(fill="x", pady=3, padx=5)
            tk.Label(f, text=f"{item.name:<20}", fg="white", bg="#2d2d2d", font=("Arial", 11, "bold")).pack(side="left",
                                                                                                            padx=15)
            tk.Label(f, text=f"{item.price:.2f}€ | Stock: {item.stock}", fg="#aaaaaa", bg="#2d2d2d").pack(side="left",
                                                                                                          padx=20)
            btn = tk.Button(f, text="Add to Cart", bg="#007acc", fg="white", relief="flat", font=("Arial", 9, "bold"),
                            padx=15, command=lambda i=item: self.add_to_cart(i))
            btn.pack(side="right", padx=15)

    def add_to_cart(self, item):
        if item.stock > 0:
            item.stock -= 1
            self.cart.append(item)
            self.total_price += item.price
            self.cart_box.insert(tk.END, f"{item.name} - {item.price:.2f}€")
            self.lbl_total.config(text=f"Total: {self.total_price:.2f} EUR")
            self.render_products()
        else:
            messagebox.showwarning("Warning", "Out of stock!")

    def remove_from_cart(self):
        try:
            index = self.cart_box.curselection()[0]
            item = self.cart.pop(index)
            item.stock += 1
            self.total_price -= item.price
            self.cart_box.delete(index)
            self.lbl_total.config(text=f"Total: {self.total_price:.2f} EUR")
            self.render_products()
        except:
            pass

    def complete_payment(self):
        if not self.cart: return
        db = sqlite3.connect(self.db_name)
        cursor = db.cursor()
        for item in set(self.cart):
            cursor.execute("UPDATE inventory SET stock = ? WHERE id = ?", (item.stock, item.code))
        db.commit()
        db.close()
        messagebox.showinfo("Success", f"Paid: {self.total_price:.2f} EUR\nStock Updated!")
        self.cart, self.total_price = [], 0.0
        self.cart_box.delete(0, tk.END)
        self.lbl_total.config(text="Total: 0.00 EUR")

    # --- ADMIN BÖLÜMÜ ---
    def admin_login(self):
        win = tk.Toplevel(self.root)
        win.title("Login")
        win.geometry("250x150")
        tk.Label(win, text="Admin Password:").pack(pady=10)
        pw = tk.Entry(win, show="*")
        pw.pack()
        tk.Button(win, text="Login", command=lambda: self.check_pw(pw.get(), win)).pack(pady=15)

    def check_pw(self, p, win):
        if p == "1234":
            win.destroy()
            self.open_admin_panel()
        else:
            messagebox.showerror("Error", "Wrong!")

    def open_admin_panel(self):
        admin_win = tk.Toplevel(self.root)
        admin_win.title("Admin Panel - Price/Stock Edit")
        admin_win.geometry("550x600")
        admin_win.configure(bg="#2d2d2d")

        canvas = tk.Canvas(admin_win, bg="#2d2d2d", highlightthickness=0)
        scr = ttk.Scrollbar(admin_win, orient="vertical", command=canvas.yview)
        frame = tk.Frame(canvas, bg="#2d2d2d")
        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scr.set)
        canvas.pack(side="left", fill="both", expand=True)
        scr.pack(side="right", fill="y")

        def save(item, p_e, s_e):
            try:
                np, ns = float(p_e.get()), int(s_e.get())
                db = sqlite3.connect(self.db_name)
                db.cursor().execute("UPDATE inventory SET price = ?, stock = ? WHERE id = ?", (np, ns, item.code))
                db.commit()
                db.close()
                item.price, item.stock = np, ns
                messagebox.showinfo("OK", f"{item.name} Updated!")
                self.render_products()
            except:
                messagebox.showerror("Error", "Invalid input!")

        for item in self.products_list:
            row = tk.Frame(frame, bg="#3d3d3d", pady=5)
            row.pack(fill="x", pady=2, padx=10)
            tk.Label(row, text=item.name, fg="white", bg="#3d3d3d", width=12).grid(row=0, column=0)
            pe = tk.Entry(row, width=6);
            pe.insert(0, str(item.price));
            pe.grid(row=0, column=1, padx=5)
            se = tk.Entry(row, width=6);
            se.insert(0, str(item.stock));
            se.grid(row=0, column=2, padx=5)
            tk.Button(row, text="Save", bg="#28a745", fg="white",
                      command=lambda i=item, p=pe, s=se: save(i, p, s)).grid(row=0, column=3, padx=10)

        frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))


if __name__ == "__main__":
    root = tk.Tk()
    app = MarketApp(root)
    root.mainloop()