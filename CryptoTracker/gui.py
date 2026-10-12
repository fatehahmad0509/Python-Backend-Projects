import customtkinter as ctk
import threading
import datetime
from main import getprices

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

CRYPTO_INFO = {
    "BTC":  {"name": "Bitcoin",   "icon": "₿", "color": "#F7931A"},
    "ETH":  {"name": "Ethereum",  "icon": "Ξ", "color": "#627EEA"},
    "USDT": {"name": "Tether",    "icon": "₮", "color": "#26A17B"},
    "BNB":  {"name": "BNB",       "icon": "◈", "color": "#F3BA2F"},
    "SOL":  {"name": "Solana",    "icon": "◎", "color": "#9945FF"},
    "XRP":  {"name": "XRP",       "icon": "✕", "color": "#346AA9"},
    "USDC": {"name": "USD Coin",  "icon": "$", "color": "#2775CA"},
    "ADA":  {"name": "Cardano",   "icon": "₳", "color": "#0033AD"},
    "DOGE": {"name": "Dogecoin",  "icon": "Ð", "color": "#C2A633"},
    "TRX":  {"name": "TRON",      "icon": "♦", "color": "#FF0013"},
}

UPDATE_INTERVAL = 10000  # 10 seconds

class CryptoApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CryptoTracker")
        self.geometry("980x680")
        self.minsize(820, 580)
        self.configure(fg_color="#0d0d0f")

        self.previous_prices = {}
        self.first_prices = {}
        self.card_widgets = {}

        self._setup_ui()
        self.after(100, self._auto_refresh_loop)

    def _setup_ui(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#111114")
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(pady=(36, 0), padx=20, fill="x")

        ctk.CTkLabel(logo_frame, text="₿", font=ctk.CTkFont(size=40, weight="bold"), text_color="#F7931A").pack()
        ctk.CTkLabel(logo_frame, text="CryptoTracker", font=ctk.CTkFont(size=22, weight="bold"), text_color="#ffffff").pack()
        ctk.CTkLabel(logo_frame, text="PRO", font=ctk.CTkFont(size=11), text_color="#F7931A").pack()

        ctk.CTkFrame(self.sidebar, height=1, fg_color="#2a2a2e").pack(fill="x", padx=20, pady=24)

        self.status_label = ctk.CTkLabel(self.sidebar, text="● LIVE", font=ctk.CTkFont(size=12), text_color="#00ff88")
        self.status_label.pack(pady=(0, 6))

        self.last_update_label = ctk.CTkLabel(self.sidebar, text="Fetching...", font=ctk.CTkFont(size=11), text_color="#666677")
        self.last_update_label.pack(pady=(0, 20))

        ctk.CTkLabel(
            self.sidebar, text="Auto-refresh every 10s", font=ctk.CTkFont(size=12), text_color="#888888"
        ).pack(pady=(12, 0), padx=20)

        ctk.CTkFrame(self.sidebar, height=1, fg_color="#2a2a2e").pack(fill="x", padx=20, pady=24)

        ctk.CTkLabel(self.sidebar, text="Top 10 Crypto\nPrices in USD", font=ctk.CTkFont(size=11),
                     text_color="#44444f", justify="center").pack()

        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(side="right", fill="both", expand=True)

        header = ctk.CTkFrame(self.main_frame, height=56, fg_color="#111114", corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="Market Prices", font=ctk.CTkFont(size=16, weight="bold"), text_color="#ffffff").pack(side="left", padx=24, pady=16)
        self.header_time = ctk.CTkLabel(header, text="", font=ctk.CTkFont(size=11), text_color="#555566")
        self.header_time.pack(side="right", padx=24)

        self.scroll_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent",
                                                   scrollbar_button_color="#2a2a2e",
                                                   scrollbar_button_hover_color="#3a3a4e")
        self.scroll_frame.pack(fill="both", expand=True, padx=16, pady=16)
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        self.scroll_frame.grid_columnconfigure(1, weight=1)

        self._build_cards()

    def _build_cards(self):
        for i, (symbol, info) in enumerate(CRYPTO_INFO.items()):
            row, col = divmod(i, 2)
            card = ctk.CTkFrame(self.scroll_frame, fg_color="#18181d", corner_radius=14, border_width=1, border_color="#2a2a2e")
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

            accent = ctk.CTkFrame(card, width=4, corner_radius=2, fg_color=info["color"])
            accent.pack(side="left", fill="y", padx=(10, 0), pady=12)

            icon_frame = ctk.CTkFrame(card, width=48, height=48, corner_radius=24, fg_color=info["color"])
            icon_frame.pack(side="left", padx=14, pady=16)
            icon_frame.pack_propagate(False)

            ctk.CTkLabel(icon_frame, text=info["icon"], font=ctk.CTkFont(size=20, weight="bold"), text_color=info["color"]).place(relx=0.5, rely=0.5, anchor="center")

            text_frame = ctk.CTkFrame(card, fg_color="transparent")
            text_frame.pack(side="left", fill="both", expand=True, pady=14)

            ctk.CTkLabel(text_frame, text=info["name"], font=ctk.CTkFont(size=12), text_color="#666677").pack(anchor="w")
            ctk.CTkLabel(text_frame, text=symbol, font=ctk.CTkFont(size=11), text_color="#44444f").pack(anchor="w")

            right_frame = ctk.CTkFrame(card, fg_color="transparent")
            right_frame.pack(side="right", padx=20, pady=14)

            price_lbl = ctk.CTkLabel(right_frame, text="$ ---", font=ctk.CTkFont(size=20, weight="bold"), text_color="#ffffff")
            price_lbl.pack(anchor="e")

            arrow_lbl = ctk.CTkLabel(right_frame, text="", font=ctk.CTkFont(size=12), text_color="#666677")
            arrow_lbl.pack(anchor="e")

            self.card_widgets[symbol] = {"price_lbl": price_lbl, "arrow_lbl": arrow_lbl}

    def _auto_refresh_loop(self):
        self._start_fetch()
        self.after(UPDATE_INTERVAL, self._auto_refresh_loop)

    def _start_fetch(self):
        self.status_label.configure(text="● UPDATING", text_color="#F7931A")
        threading.Thread(target=self._fetch_data, daemon=True).start()

    def _fetch_data(self):
        try:
            prices = getprices()
            self.after(0, lambda: self._update_ui(prices))
        except Exception as e:
            self.after(0, lambda: self._handle_error(str(e)))

    def _update_ui(self, prices: dict):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.last_update_label.configure(text=f"Last: {now}")
        self.header_time.configure(text=f"Last updated: {now}")
        self.status_label.configure(text="● LIVE", text_color="#00ff88")

        for symbol, price in prices.items():
            if symbol not in self.card_widgets:
                continue

            widgets = self.card_widgets[symbol]
            price_lbl = widgets["price_lbl"]
            arrow_lbl = widgets["arrow_lbl"]

            if price >= 1000:
                price_str = f"$ {price:,.2f}"
            elif price >= 1:
                price_str = f"$ {price:.4f}"
            else:
                price_str = f"$ {price:.6f}"

            price_lbl.configure(text=price_str)

            # İlk fiyatı kaydet
            if symbol not in self.first_prices:
                self.first_prices[symbol] = price

            first_price = self.first_prices[symbol]
            change = price - first_price
            percent = (change / first_price) * 100 if first_price != 0 else 0

            if change > 0:
                arrow_lbl.configure(text=f"▲ {percent:.2f}%", text_color="#00cc66")
                price_lbl.configure(text_color="#00cc66")
                self.after(1500, lambda l=price_lbl: l.configure(text_color="#ffffff"))
            elif change < 0:
                arrow_lbl.configure(text=f"▼ {abs(percent):.2f}%", text_color="#ff4455")
                price_lbl.configure(text_color="#ff4455")
                self.after(1500, lambda l=price_lbl: l.configure(text_color="#ffffff"))
            else:
                arrow_lbl.configure(text="─ No change", text_color="#555566")

        self.previous_prices = dict(prices)

    def _handle_error(self, msg=""):
        self.status_label.configure(text="● CONNECTION ERROR", text_color="#ff4455")
        print(f"[CryptoTracker] Error: {msg}")


if __name__ == "__main__":
    app = CryptoApp()
    app.mainloop()
