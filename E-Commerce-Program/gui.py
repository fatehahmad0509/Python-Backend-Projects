import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, font
import time

# ─────────────────────────────────────────────
#  THEME COLORS
# ─────────────────────────────────────────────
BG        = "#0d0d14"
CARD      = "#16162a"
SIDEBAR   = "#11111f"
ACCENT    = "#6c47ff"
ACCENT2   = "#3b82f6"
HOVER     = "#8a6aff"
TEXT      = "#e8e8f0"
SUBTEXT   = "#8888aa"
SUCCESS   = "#22c55e"
DANGER    = "#ef4444"
BORDER    = "#2a2a45"
BADGE     = "#ff3b5c"

# ─────────────────────────────────────────────
#  DATA FILES
# ─────────────────────────────────────────────
ACCOUNT_FILE = "accountinfos.json"
BALANCE_FILE  = "balance.json"
STOCKS_FILE   = "stocks.json"

# ─────────────────────────────────────────────
#  PRODUCTS
# ─────────────────────────────────────────────
PRODUCTS = [
    {"id":1,  "name":"Bread",           "price":1.0,  "emoji":"🍞", "cat":"Food"},
    {"id":2,  "name":"Milk (1L)",        "price":2.0,  "emoji":"🥛", "cat":"Food"},
    {"id":3,  "name":"Egg (10)",         "price":4.0,  "emoji":"🥚", "cat":"Food"},
    {"id":4,  "name":"Rice (1KG)",       "price":5.0,  "emoji":"🍚", "cat":"Food"},
    {"id":5,  "name":"Pasta",            "price":2.5,  "emoji":"🍝", "cat":"Food"},
    {"id":6,  "name":"Gouda Cheese",     "price":7.0,  "emoji":"🧀", "cat":"Food"},
    {"id":7,  "name":"Stroopwafel",      "price":4.0,  "emoji":"🧇", "cat":"Snack"},
    {"id":8,  "name":"Organic Milk",     "price":3.0,  "emoji":"🐄", "cat":"Food"},
    {"id":9,  "name":"Protein Bar",      "price":3.0,  "emoji":"💪", "cat":"Snack"},
    {"id":10, "name":"Water (500ML)",    "price":1.0,  "emoji":"💧", "cat":"Beverage"},
    {"id":11, "name":"Fruit Juice",      "price":2.5,  "emoji":"🍊", "cat":"Beverage"},
    {"id":12, "name":"Coffee",           "price":4.0,  "emoji":"☕", "cat":"Beverage"},
    {"id":13, "name":"Frozen Pizza",     "price":5.0,  "emoji":"🍕", "cat":"Fastfood"},
    {"id":14, "name":"Sandwich",         "price":3.0,  "emoji":"🥪", "cat":"Fastfood"},
    {"id":15, "name":"Microwave Meal",   "price":7.0,  "emoji":"🍱", "cat":"Fastfood"},
    {"id":16, "name":"Detergent",        "price":8.0,  "emoji":"🧼", "cat":"Clean"},
    {"id":17, "name":"Toilet Paper",     "price":6.0,  "emoji":"🧻", "cat":"Clean"},
    {"id":18, "name":"Shampoo",          "price":7.0,  "emoji":"🧴", "cat":"Clean"},
    {"id":19, "name":"Coca Cola",        "price":4.0,  "emoji":"🥤", "cat":"Beverage"},
]

DEFAULT_STOCK = 1000

# ─────────────────────────────────────────────
#  PERSISTENCE HELPERS
# ─────────────────────────────────────────────
def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_stocks():
    raw = load_json(STOCKS_FILE, {})
    stocks = {}
    for p in PRODUCTS:
        key = p["name"].lower().replace(" ", "").replace("(", "").replace(")", "").replace("'", "").replace(",","")
        # Try english key first for backward compat
        eng_keys = {1:"bread",2:"milk",3:"egg",4:"rice",5:"pasta",6:"goudacheese",7:"stroopwafel",
                    8:"organicmilk",9:"proteinbar",10:"water",11:"fruitjuice",12:"coffee",
                    13:"frozenpizza",14:"sandwich",15:"microwavemeal",16:"detergent",
                    17:"toiletpaper",18:"shampoo",19:"cocacola"}
        ek = eng_keys.get(p["id"], key)
        stocks[p["id"]] = raw.get(ek, DEFAULT_STOCK)
        # price override
        pp = raw.get(ek + "_price", None)
        if pp is not None:
            p["price"] = pp
    return stocks

def save_stocks(stocks):
    eng_keys = {1:"bread",2:"milk",3:"egg",4:"rice",5:"pasta",6:"goudacheese",7:"stroopwafel",
                8:"organicmilk",9:"proteinbar",10:"water",11:"fruitjuice",12:"coffee",
                13:"frozenpizza",14:"sandwich",15:"microwavemeal",16:"detergent",
                17:"toiletpaper",18:"shampoo",19:"cocacola"}
    out = {}
    for p in PRODUCTS:
        ek = eng_keys[p["id"]]
        out[ek] = stocks.get(p["id"], DEFAULT_STOCK)
        out[ek + "_price"] = p["price"]
    save_json(STOCKS_FILE, out)

# ─────────────────────────────────────────────
#  STYLED WIDGET HELPERS
# ─────────────────────────────────────────────
def styled_button(parent, text, command, bg=ACCENT, fg=TEXT, width=None, padx=18, pady=9, font_size=11, bold=True):
    f = ("Segoe UI", font_size, "bold" if bold else "normal")
    kw = dict(text=text, command=command, bg=bg, fg=fg, relief="flat",
              cursor="hand2", font=f, padx=padx, pady=pady,
              activebackground=HOVER, activeforeground=TEXT, bd=0)
    if width:
        kw["width"] = width
    btn = tk.Button(parent, **kw)
    btn.bind("<Enter>", lambda e: btn.config(bg=HOVER if bg==ACCENT else bg))
    btn.bind("<Leave>", lambda e: btn.config(bg=bg))
    return btn

def styled_entry(parent, textvariable=None, show=None, width=30):
    kw = dict(bg="#1e1e35", fg=TEXT, insertbackground=TEXT, relief="flat",
              font=("Segoe UI", 11), bd=0, highlightthickness=1,
              highlightbackground=BORDER, highlightcolor=ACCENT, width=width)
    if textvariable:
        kw["textvariable"] = textvariable
    if show:
        kw["show"] = show
    e = tk.Entry(parent, **kw)
    return e

def label(parent, text, size=11, color=TEXT, bold=False, wrap=0):
    f = ("Segoe UI", size, "bold" if bold else "normal")
    kw = dict(text=text, bg=BG, fg=color, font=f)
    if wrap:
        kw["wraplength"] = wrap
    return tk.Label(parent, **kw)

def card_frame(parent, bg=CARD, bd=0, pad=0):
    f = tk.Frame(parent, bg=bg, bd=bd, highlightthickness=1,
                 highlightbackground=BORDER)
    if pad:
        f.config(padx=pad, pady=pad)
    return f

# ─────────────────────────────────────────────
#  MAIN APP
# ─────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ecommerce.com")
        self.geometry("1100x720")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.minsize(900, 600)

        self.account = load_json(ACCOUNT_FILE, None)
        self.balance = load_json(BALANCE_FILE, 0)
        self.stocks  = load_stocks()
        self.cart    = []  # list of product dicts (copy with qty)

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Vertical.TScrollbar",
                        background=BORDER, troughcolor=SIDEBAR,
                        bordercolor=SIDEBAR, arrowcolor=SUBTEXT,
                        relief="flat")

        self._container = tk.Frame(self, bg=BG)
        self._container.pack(fill="both", expand=True)

        if self.account is None:
            self.show_signup()
        else:
            self.show_login()

    # ── PAGE SWITCHING ──────────────────────────
    def clear(self):
        for w in self._container.winfo_children():
            w.destroy()

    def show_login(self):
        self.clear()
        LoginPage(self._container, self)

    def show_signup(self):
        self.clear()
        SignupPage(self._container, self)

    def show_main(self):
        self.clear()
        MainPage(self._container, self)

    def show_shop(self):
        self.clear()
        ShopPage(self._container, self)

    def show_cart(self):
        self.clear()
        CartPage(self._container, self)

    def show_balance(self):
        self.clear()
        BalancePage(self._container, self)

    # ── DATA SHORTCUTS ──────────────────────────
    def save_balance(self):
        save_json(BALANCE_FILE, self.balance)

    def save_account(self):
        save_json(ACCOUNT_FILE, self.account)

    def save_stocks(self):
        save_stocks(self.stocks)

# ─────────────────────────────────────────────
#  AUTH PAGES
# ─────────────────────────────────────────────
class AuthBase(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        pass

    def center_card(self, width=420):
        outer = tk.Frame(self, bg=BG)
        outer.place(relx=0.5, rely=0.5, anchor="center")
        card = card_frame(outer, pad=36)
        card.pack()
        return card

    def logo(self, parent):
        tk.Label(parent, text="🛒  Ecommerce.com", bg=CARD,
                 fg=ACCENT, font=("Segoe UI", 20, "bold")).pack(pady=(0, 4))
        tk.Label(parent, text="The new address of shopping!", bg=CARD,
                 fg=SUBTEXT, font=("Segoe UI", 10)).pack(pady=(0, 24))

    def field(self, parent, label_text, show=None):
        tk.Label(parent, text=label_text, bg=CARD, fg=SUBTEXT,
                 font=("Segoe UI", 9)).pack(anchor="w")
        e = styled_entry(parent, show=show)
        e.pack(fill="x", pady=(2, 12), ipady=8)
        return e

    def divider(self, parent):
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=12)

class LoginPage(AuthBase):
    def _build(self):
        card = self.center_card()
        self.logo(card)
        tk.Label(card, text="Log In", bg=CARD, fg=TEXT,
                 font=("Segoe UI", 15, "bold")).pack(anchor="w", pady=(0,16))
        self.pw = self.field(card, "Password", show="•")
        err_lbl = tk.Label(card, text="", bg=CARD, fg=DANGER,
                           font=("Segoe UI", 9))
        err_lbl.pack(anchor="w", pady=(0,8))

        def do_login():
            if self.pw.get() == self.app.account.get("password", ""):
                self.app.show_main()
            else:
                err_lbl.config(text="Wrong password. Try again.")
                self.pw.delete(0, "end")

        styled_button(card, "Log In", do_login).pack(fill="x", pady=4)
        self.divider(card)
        tk.Label(card, text="Don't have an account?", bg=CARD, fg=SUBTEXT,
                 font=("Segoe UI", 9)).pack()
        styled_button(card, "Sign Up", self.app.show_signup,
                      bg=BORDER, pady=6, font_size=10).pack(fill="x", pady=6)

class SignupPage(AuthBase):
    def _build(self):
        card = self.center_card(480)
        self.logo(card)
        tk.Label(card, text="Sign Up", bg=CARD, fg=TEXT,
                 font=("Segoe UI", 15, "bold")).pack(anchor="w", pady=(0,16))
        self.name  = self.field(card, "Full Name")
        self.email = self.field(card, "E-Mail")
        self.pw    = self.field(card, "Password", show="•")
        self.bdate = self.field(card, "Birthdate (MM.DD.YYYY)")
        self.age   = self.field(card, "Age")
        err_lbl = tk.Label(card, text="", bg=CARD, fg=DANGER,
                           font=("Segoe UI", 9))
        err_lbl.pack(anchor="w", pady=(0,8))

        def do_signup():
            if not all([self.name.get(), self.email.get(), self.pw.get()]):
                err_lbl.config(text="Please fill in all fields.")
                return
            info = {
                "name": self.name.get(),
                "email": self.email.get(),
                "password": self.pw.get(),
                "birthdate": self.bdate.get(),
                "age": self.age.get(),
            }
            self.app.account = info
            self.app.save_account()
            self.app.show_login()

        styled_button(card, "Sign Up", do_signup).pack(fill="x", pady=4)
        self.divider(card)
        tk.Label(card, text="Already have an account?", bg=CARD, fg=SUBTEXT,
                 font=("Segoe UI", 9)).pack()
        styled_button(card, "Log In", self.app.show_login,
                      bg=BORDER, pady=6, font_size=10).pack(fill="x", pady=6)

# ─────────────────────────────────────────────
#  MAIN MENU
# ─────────────────────────────────────────────
class MainPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        self._navbar()
        self._hero()
        self._cards()

    def _navbar(self):
        nav = tk.Frame(self, bg=SIDEBAR, height=60)
        nav.pack(fill="x")
        nav.pack_propagate(False)
        tk.Label(nav, text="🛒  Ecommerce.com", bg=SIDEBAR, fg=ACCENT,
                 font=("Segoe UI", 16, "bold")).pack(side="left", padx=20)
        # Balance badge
        bal_txt = f"💰  {self.app.balance:.2f} €"
        tk.Label(nav, text=bal_txt, bg=SIDEBAR, fg=SUCCESS,
                 font=("Segoe UI", 12, "bold")).pack(side="right", padx=16)
        name = self.app.account.get("name", "User").split()[0]
        tk.Label(nav, text=f"👤 {name}", bg=SIDEBAR, fg=TEXT,
                 font=("Segoe UI", 11)).pack(side="right", padx=8)

    def _hero(self):
        hero = tk.Frame(self, bg=ACCENT, height=140)
        hero.pack(fill="x")
        hero.pack_propagate(False)
        tk.Label(hero, text="Good Shopping! 🎉", bg=ACCENT, fg="white",
                 font=("Segoe UI", 22, "bold")).pack(pady=(28,4))
        tk.Label(hero, text="Create your cart, pay, and receive.", bg=ACCENT, fg="#d4c9ff",
                 font=("Segoe UI", 11)).pack()

    def _cards(self):
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=40, pady=32)

        items = [
            ("🛍️", "Shop",   "Browse and add products to your cart.",    self.app.show_shop,    ACCENT),
            ("💳", "Top Up / Withdraw", "Manage your account balance.",                self.app.show_balance, "#2563eb"),
            ("🛒", "My Cart",          f"{len(self.app.cart)} item(s) in cart", self.app.show_cart,    "#7c3aed"),
            ("🚪", "Log Out",        "Safe log out.",                   self._logout,          "#374151"),
        ]

        for i, (emoji, title, sub, cmd, color) in enumerate(items):
            col = i % 2
            row = i // 2
            c = card_frame(body, pad=24)
            c.grid(row=row, column=col, padx=12, pady=12, sticky="nsew")
            body.columnconfigure(col, weight=1)
            body.rowconfigure(row, weight=1)

            tk.Label(c, text=emoji, bg=CARD, fg=color,
                     font=("Segoe UI", 32)).pack(anchor="w")
            tk.Label(c, text=title, bg=CARD, fg=TEXT,
                     font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(8,2))
            tk.Label(c, text=sub, bg=CARD, fg=SUBTEXT,
                     font=("Segoe UI", 10)).pack(anchor="w", pady=(0,14))
            styled_button(c, "Go →", cmd, bg=color, pady=7,
                          font_size=10).pack(anchor="w")

    def _logout(self):
        self.app.show_login()

# ─────────────────────────────────────────────
#  SHOP PAGE
# ─────────────────────────────────────────────
class ShopPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self.pack(fill="both", expand=True)
        self.filter_cat = tk.StringVar(value="All")
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self._render_products())
        self._build()

    def _build(self):
        self._navbar()
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)
        self._sidebar(body)
        self._main(body)

    def _navbar(self):
        nav = tk.Frame(self, bg=SIDEBAR, height=56)
        nav.pack(fill="x")
        nav.pack_propagate(False)
        styled_button(nav, "← Back", self.app.show_main,
                      bg=BORDER, pady=6, font_size=10, padx=12).pack(side="left", padx=12, pady=8)
        tk.Label(nav, text="🛍️  Products", bg=SIDEBAR, fg=TEXT,
                 font=("Segoe UI", 14, "bold")).pack(side="left", padx=8)
        cart_count = sum(item["qty"] for item in self.app.cart)
        self._cart_btn = styled_button(nav, f"🛒  Cart ({cart_count})", self.app.show_cart,
                                       bg=ACCENT, pady=6, font_size=10)
        self._cart_btn.pack(side="right", padx=12, pady=8)
        tk.Label(nav, text=f"💰 {self.app.balance:.2f} €", bg=SIDEBAR,
                 fg=SUCCESS, font=("Segoe UI", 11, "bold")).pack(side="right", padx=10)
    def _sidebar(self, body):
        sb = tk.Frame(body, bg=SIDEBAR, width=180)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)
        tk.Label(sb, text="Categories", bg=SIDEBAR, fg=SUBTEXT,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16, pady=(20,8))
        cats = ["All"] + sorted(set(p["cat"] for p in PRODUCTS))
        for cat in cats:
            def make_cmd(c):
                def cmd():
                    self.filter_cat.set(c)
                    self._render_products()
                return cmd
            btn = tk.Button(sb, text=cat, command=make_cmd(cat),
                            bg=SIDEBAR, fg=TEXT, relief="flat",
                            font=("Segoe UI", 10), anchor="w",
                            padx=16, pady=6, cursor="hand2",
                            activebackground=BORDER, activeforeground=TEXT, bd=0)
            btn.pack(fill="x")
            # highlight selected
            if cat == self.filter_cat.get():
                btn.config(bg=ACCENT, fg="white")

    def _main(self, body):
        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        # search bar
        search_bar = tk.Frame(right, bg=BG)
        search_bar.pack(fill="x", padx=20, pady=14)
        tk.Label(search_bar, text="🔍", bg=BG, fg=SUBTEXT,
                 font=("Segoe UI", 12)).pack(side="left", padx=(0,6))
        se = styled_entry(search_bar, textvariable=self.search_var, width=40)
        se.pack(side="left", ipady=7, fill="x", expand=True)

        # scrollable product grid
        canvas_frame = tk.Frame(right, bg=BG)
        canvas_frame.pack(fill="both", expand=True, padx=16)

        self.canvas = tk.Canvas(canvas_frame, bg=BG, bd=0,
                                highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical",
                                   command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.grid_frame = tk.Frame(self.canvas, bg=BG)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.grid_frame, anchor="nw")

        self.grid_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self._render_products()

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _render_products(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()
        cat = self.filter_cat.get()
        q = self.search_var.get().lower()
        filtered = [p for p in PRODUCTS
                    if (cat == "All" or p["cat"] == cat)
                    and q in p["name"].lower()]
        cols = 4
        for i, p in enumerate(filtered):
            row, col = divmod(i, cols)
            self._product_card(self.grid_frame, p, row, col)
            self.grid_frame.columnconfigure(col, weight=1)

    def _product_card(self, parent, p, row, col):
        stock = self.app.stocks.get(p["id"], DEFAULT_STOCK)
        c = tk.Frame(parent, bg=CARD, highlightthickness=1,
                     highlightbackground=BORDER, cursor="hand2")
        c.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        # emoji big
        tk.Label(c, text=p["emoji"], bg=CARD, fg=TEXT,
                 font=("Segoe UI", 28)).pack(pady=(14,4))
        tk.Label(c, text=p["name"], bg=CARD, fg=TEXT,
                 font=("Segoe UI", 10, "bold"), wraplength=120,
                 justify="center").pack(padx=8)
        tk.Label(c, text=p["cat"], bg=CARD, fg=SUBTEXT,
                 font=("Segoe UI", 8)).pack()

        # stock indicator
        stock_color = SUCCESS if stock > 10 else (ACCENT if stock > 0 else DANGER)
        stock_txt = f"Stock: {stock}" if stock > 0 else "Out of Stock"
        tk.Label(c, text=stock_txt, bg=CARD, fg=stock_color,
                 font=("Segoe UI", 8)).pack(pady=2)

        tk.Label(c, text=f"{p['price']:.2f} €", bg=CARD, fg=ACCENT,
                 font=("Segoe UI", 13, "bold")).pack(pady=4)

        def add(pid=p["id"]):
            self._add_to_cart(pid)

        btn = styled_button(c, "Add To Cart" if stock > 0 else "Out of Stock",
                            add if stock > 0 else lambda: None,
                            bg=ACCENT if stock > 0 else "#374151",
                            pady=5, font_size=9, padx=10)
        btn.pack(padx=10, pady=(2,14), fill="x")

    def _add_to_cart(self, pid):
        stock = self.app.stocks.get(pid, DEFAULT_STOCK)
        if stock <= 0:
            messagebox.showwarning("Out of Stock", "This product is out of stock.")
            return
        # check cart qty
        in_cart = sum(i["qty"] for i in self.app.cart if i["id"] == pid)
        if in_cart >= stock:
            messagebox.showwarning("Insufficient Stock", "Not enough stock.")
            return
        for item in self.app.cart:
            if item["id"] == pid:
                item["qty"] += 1
                self._flash_cart()
                return
        prod = next(p for p in PRODUCTS if p["id"] == pid)
        self.app.cart.append({**prod, "qty": 1})
        self._flash_cart()

    def _flash_cart(self):
        self._render_products()
        cart_count = sum(item["qty"] for item in self.app.cart)
        self._cart_btn.config(text=f"🛒  Cart ({cart_count})")

# ─────────────────────────────────────────────
#  CART PAGE
# ─────────────────────────────────────────────
class CartPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        nav = tk.Frame(self, bg=SIDEBAR, height=56)
        nav.pack(fill="x")
        nav.pack_propagate(False)
        styled_button(nav, "← Continue Shopping", self.app.show_shop,
                      bg=BORDER, pady=6, font_size=10, padx=12).pack(side="left", padx=12, pady=8)
        tk.Label(nav, text="🛒  My Cart", bg=SIDEBAR, fg=TEXT,
                 font=("Segoe UI", 14, "bold")).pack(side="left", padx=8)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=32, pady=24)

        # Left: item list
        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="both", expand=True)

        if not self.app.cart:
            tk.Label(left, text="🛒", bg=BG, fg=SUBTEXT,
                     font=("Segoe UI", 48)).pack(pady=40)
            tk.Label(left, text="Your cart is empty.", bg=BG, fg=SUBTEXT,
                     font=("Segoe UI", 14)).pack()
            styled_button(left, "Start Shopping", self.app.show_shop,
                          pady=9).pack(pady=20)
            return

        # header
        hdr = tk.Frame(left, bg=BG)
        hdr.pack(fill="x", pady=(0,8))
        for col, txt, w in [("Product","",240),("Price","",80),("Qty","",80),("Total","",90),("","",50)]:
            tk.Label(hdr, text=txt or col, bg=BG, fg=SUBTEXT,
                     font=("Segoe UI", 9, "bold"), width=w//7,
                     anchor="w").pack(side="left", padx=4)

        self.items_frame = tk.Frame(left, bg=BG)
        self.items_frame.pack(fill="both")
        self._render_items()

        # Right: summary
        right = card_frame(body, pad=24)
        right.pack(side="right", fill="y", padx=(24,0), anchor="n")
        self._summary(right)

    def _render_items(self):
        for w in self.items_frame.winfo_children():
            w.destroy()
        for item in self.app.cart:
            row = card_frame(self.items_frame, pad=12)
            row.pack(fill="x", pady=4)
            tk.Label(row, text=f"{item['emoji']}  {item['name']}", bg=CARD,
                     fg=TEXT, font=("Segoe UI", 11), anchor="w",
                     width=28).pack(side="left", padx=6)
            tk.Label(row, text=f"{item['price']:.2f} €", bg=CARD,
                     fg=SUBTEXT, font=("Segoe UI", 10), width=8).pack(side="left")

            # qty controls
            def make_dec(i):
                def dec():
                    if i["qty"] > 1:
                        i["qty"] -= 1
                    else:
                        self.app.cart.remove(i)
                    self._render_items()
                    self._refresh_summary()
                return dec
            def make_inc(i):
                def inc():
                    stock = self.app.stocks.get(i["id"], DEFAULT_STOCK)
                    if i["qty"] < stock:
                        i["qty"] += 1
                    self._render_items()
                    self._refresh_summary()
                return inc
            def make_del(i):
                def d():
                    self.app.cart.remove(i)
                    self._render_items()
                    self._refresh_summary()
                    if not self.app.cart:
                        self.app.show_cart()
                return d

            ctrl = tk.Frame(row, bg=CARD)
            ctrl.pack(side="left", padx=8)
            tk.Button(ctrl, text="−", bg=BORDER, fg=TEXT, relief="flat",
                      font=("Segoe UI",10,"bold"), command=make_dec(item),
                      cursor="hand2", padx=8, pady=2).pack(side="left")
            tk.Label(ctrl, text=str(item["qty"]), bg=CARD, fg=TEXT,
                     font=("Segoe UI",10), width=3,
                     anchor="center").pack(side="left")
            tk.Button(ctrl, text="+", bg=ACCENT, fg="white", relief="flat",
                      font=("Segoe UI",10,"bold"), command=make_inc(item),
                      cursor="hand2", padx=8, pady=2).pack(side="left")

            total = item["price"] * item["qty"]
            tk.Label(row, text=f"{total:.2f} €", bg=CARD, fg=ACCENT,
                     font=("Segoe UI", 11, "bold"), width=9).pack(side="left", padx=8)
            tk.Button(row, text="🗑", bg=CARD, fg=DANGER, relief="flat",
                      font=("Segoe UI",12), command=make_del(item),
                      cursor="hand2").pack(side="right", padx=6)

    def _summary(self, parent):
        tk.Label(parent, text="Order Summary", bg=CARD, fg=TEXT,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0,16))
        self.sum_frame = tk.Frame(parent, bg=CARD)
        self.sum_frame.pack(fill="x")
        self._draw_summary()

    def _draw_summary(self):
        for w in self.sum_frame.winfo_children():
            w.destroy()
        total = sum(i["price"] * i["qty"] for i in self.app.cart)
        items_count = sum(i["qty"] for i in self.app.cart)
        tk.Label(self.sum_frame, text=f"Number of products: {items_count}", bg=CARD,
                 fg=SUBTEXT, font=("Segoe UI", 10)).pack(anchor="w", pady=2)
        tk.Label(self.sum_frame, text=f"Total:", bg=CARD,
                 fg=SUBTEXT, font=("Segoe UI", 10)).pack(anchor="w", pady=2)
        tk.Label(self.sum_frame, text=f"  {total:.2f} €", bg=CARD,
                 fg=TEXT, font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=2)
        tk.Frame(self.sum_frame, bg=BORDER, height=1).pack(fill="x", pady=8)
        bal = self.app.balance
        tk.Label(self.sum_frame, text=f"Your balance: {bal:.2f} €", bg=CARD,
                 fg=SUCCESS if bal >= total else DANGER,
                 font=("Segoe UI", 10)).pack(anchor="w", pady=2)

        def checkout():
            if not self.app.cart:
                return
            total2 = sum(i["price"] * i["qty"] for i in self.app.cart)
            if self.app.balance < total2:
                messagebox.showerror("Insufficient Balance",
                    f"Balance insufficient.\nBalance: {self.app.balance:.2f} €\nTotal: {total2:.2f} €")
                return
            # deduct stock
            for item in self.app.cart:
                self.app.stocks[item["id"]] = self.app.stocks.get(item["id"], DEFAULT_STOCK) - item["qty"]
            self.app.balance -= total2
            self.app.save_balance()
            self.app.save_stocks()
            self._show_receipt(total2)

        styled_button(self.sum_frame, f"Complete Payment  {total:.2f} €",
                      checkout, pady=11).pack(fill="x", pady=(12,4))
        styled_button(self.sum_frame, "Clear Cart",
                      self._clear_cart, bg=DANGER, pady=7,
                      font_size=10).pack(fill="x")

    def _refresh_summary(self):
        self._draw_summary()

    def _clear_cart(self):
        self.app.cart.clear()
        self.app.show_cart()

    def _show_receipt(self, total):
        snapshot = list(self.app.cart)
        self.app.cart.clear()

        win = tk.Toplevel(self)
        win.title("Payment Confirmed")
        win.configure(bg=CARD)
        win.geometry("420x540")
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text="✅", bg=CARD, fg=SUCCESS,
                 font=("Segoe UI", 40)).pack(pady=(28,4))
        tk.Label(win, text="Payment Successful!", bg=CARD, fg=TEXT,
                 font=("Segoe UI", 18, "bold")).pack()
        tk.Label(win, text="Thanks for your shopping!", bg=CARD,
                 fg=SUBTEXT, font=("Segoe UI", 10)).pack(pady=(2,18))

        tk.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=24)
        tk.Label(win, text="Receipt", bg=CARD, fg=SUBTEXT,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=28, pady=(10,4))

        f = tk.Frame(win, bg=CARD)
        f.pack(fill="x", padx=28)
        for item in snapshot:
            row = tk.Frame(f, bg=CARD)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=f"{item['emoji']} {item['name']} x{item['qty']}",
                     bg=CARD, fg=TEXT, font=("Segoe UI", 10), anchor="w").pack(side="left")
            tk.Label(row, text=f"{item['price']*item['qty']:.2f} €",
                     bg=CARD, fg=ACCENT, font=("Segoe UI", 10, "bold")).pack(side="right")

        tk.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=24, pady=8)
        total_row = tk.Frame(win, bg=CARD)
        total_row.pack(fill="x", padx=28)
        tk.Label(total_row, text="TOTAL", bg=CARD, fg=TEXT,
                 font=("Segoe UI", 12, "bold")).pack(side="left")
        tk.Label(total_row, text=f"{total:.2f} €", bg=CARD, fg=ACCENT,
                 font=("Segoe UI", 14, "bold")).pack(side="right")
        tk.Label(win, text=f"Remaining Balance: {self.app.balance:.2f} €", bg=CARD,
                 fg=SUCCESS, font=("Segoe UI", 10)).pack(pady=(12,4))

        def close():
            win.destroy()
            self.app.show_main()

        styled_button(win, "Back to Main Menu", close, pady=9).pack(
            padx=28, pady=16, fill="x")

# ─────────────────────────────────────────────
#  BALANCE PAGE
# ─────────────────────────────────────────────
class BalancePage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        nav = tk.Frame(self, bg=SIDEBAR, height=56)
        nav.pack(fill="x")
        nav.pack_propagate(False)
        styled_button(nav, "← Back", self.app.show_main,
                      bg=BORDER, pady=6, font_size=10, padx=12).pack(side="left", padx=12, pady=8)
        tk.Label(nav, text="💳  Balance Management", bg=SIDEBAR, fg=TEXT,
                 font=("Segoe UI", 14, "bold")).pack(side="left", padx=8)

        outer = tk.Frame(self, bg=BG)
        outer.place(relx=0.5, rely=0.5, anchor="center")

        card = card_frame(outer, pad=36)
        card.pack()

        # Current balance display
        tk.Label(card, text="Current Balance", bg=CARD, fg=SUBTEXT,
                 font=("Segoe UI", 11)).pack()
        self.bal_label = tk.Label(card, text=f"{self.app.balance:.2f} €",
                                   bg=CARD, fg=SUCCESS,
                                   font=("Segoe UI", 36, "bold"))
        self.bal_label.pack(pady=(4, 24))

        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", pady=4)

        tk.Label(card, text="Amount (€)", bg=CARD, fg=SUBTEXT,
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(12,2))
        self.amount_var = tk.StringVar()
        e = styled_entry(card, textvariable=self.amount_var)
        e.pack(fill="x", ipady=8, pady=(0,12))

        self.msg = tk.Label(card, text="", bg=CARD, fg=DANGER,
                            font=("Segoe UI", 9))
        self.msg.pack(anchor="w", pady=(0,6))

        styled_button(card, "Top Up", self._topup, pady=9).pack(fill="x", pady=4)
        styled_button(card, "Withdraw", self._withdraw,
                      bg="#1d4ed8", pady=9).pack(fill="x", pady=4)

    def _parse_amount(self):
        raw = self.amount_var.get().strip().replace(",", ".")
        try:
            v = float(raw)
            if v <= 0:
                raise ValueError
            return v
        except (ValueError, TypeError):
            self.msg.config(text="Enter a valid amount.", fg=DANGER)
            return None

    def _topup(self):
        v = self._parse_amount()
        if v is None:
            return
        self.app.balance += v
        self.app.save_balance()
        self.bal_label.config(text=f"{self.app.balance:.2f} €")
        self.msg.config(text=f"{v:.2f} € topped up.", fg=SUCCESS)
        self.amount_var.set("")

    def _withdraw(self):
        v = self._parse_amount()
        if v is None:
            return
        if v > self.app.balance:
            self.msg.config(text="Balance insufficient.", fg=DANGER)
            return
        self.app.balance -= v
        self.app.save_balance()
        self.bal_label.config(text=f"{self.app.balance:.2f} €")
        self.msg.config(text=f"{v:.2f} € withdrawn.", fg=SUCCESS)
        self.amount_var.set("")

# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()