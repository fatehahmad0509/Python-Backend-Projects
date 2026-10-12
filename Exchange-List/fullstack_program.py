import customtkinter as ctk
import requests
from PIL import Image
import io
import threading
import os  

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ExchangeApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Exchange.Com")
        self.geometry("900x600")
        self.configure(fg_color="#1a1a1a")

        self.api_key = "37a7c759381d6de8cc36abb7"
        self.url = f"https://v6.exchangerate-api.com/v6/{self.api_key}/latest/USD"

        self.currencies = {
            "USD": "US",
            "EUR": "local:european_union.png",  
            "GBP": "GB",
            "AZN": "AZ",
            "JPY": "JP",
            "CHF": "CH",
            "AUD": "AU",
            "CAD": "CA",
            "CNY": "CN",
            "NZD": "NZ"
        }

        self.setup_ui()
        self.after(100, self.start_thread)

    def setup_ui(self):
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#111111")
        self.sidebar.pack(side="left", fill="y")

        self.logo = ctk.CTkLabel(self.sidebar, text="GLOBAL\nEXCHANGE",
                                 font=ctk.CTkFont(size=24, weight="bold"), text_color="#D4AF37")
        self.logo.pack(pady=30)

        self.btn_update = ctk.CTkButton(self.sidebar, text="Update Now",
                                        fg_color="#D4AF37", text_color="black",
                                        hover_color="#B8962E", command=self.start_thread)
        self.btn_update.pack(pady=20, padx=20)

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)

    def start_thread(self):
        self.btn_update.configure(state="disabled", text="Loading...")
        threading.Thread(target=self.fetch_data, daemon=True).start()

    def fetch_data(self):
        try:
            response = requests.get(self.url, timeout=15)
            data = response.json()

            if data["result"] == "success":
                rates = data["conversion_rates"]
                base_to_try = rates["TRY"]
                self.after(0, lambda: self.render_ui(rates, base_to_try))
            else:
                self.after(0, self.handle_error)
        except:
            self.after(0, self.handle_error)

    def handle_error(self):
        self.btn_update.configure(state="normal", text="Error! Retry")

    def render_ui(self, rates, base_to_try):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        row, col = 0, 0
        for symbol, country_info in self.currencies.items():
            value = base_to_try if symbol == "USD" else base_to_try / rates[symbol]
            self.add_card(symbol, country_info, value, row, col)

            col += 1
            if col > 1:
                col = 0
                row += 1

        self.btn_update.configure(state="normal", text="Update Now")

    def add_card(self, symbol, country_info, value, row, col):
        card = ctk.CTkFrame(self.scroll_frame, fg_color="#252525", corner_radius=15)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        self.scroll_frame.grid_columnconfigure(col, weight=1)

        raw_data = None
        img_obj = None

        if country_info.startswith("local:"):
            file_name = country_info.split(":")[1]
            if os.path.exists(file_name):
                try:
                    raw_data = Image.open(file_name)
                    img_obj = ctk.CTkImage(light_image=raw_data, dark_image=raw_data, size=(40, 30))
                except Exception as e:
                    print(f"Error loading local image {file_name}: {e}")
        else:
            try:
                img_url = f"https://flagsapi.com/{country_info}/flat/64.png"
                img_res = requests.get(img_url, timeout=5)
                raw_data = Image.open(io.BytesIO(img_res.content))
                img_obj = ctk.CTkImage(light_image=raw_data, dark_image=raw_data, size=(40, 30))
            except Exception as e:
                print(f"Error downloading image for {symbol}: {e}")

        if img_obj:
            ctk.CTkLabel(card, image=img_obj, text="").pack(side="left", padx=15, pady=20)
        else:
            ctk.CTkLabel(card, text="🏳️").pack(side="left", padx=15, pady=20)

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(info, text=f"{symbol} / TRY", font=ctk.CTkFont(size=13), text_color="gray").pack(anchor="w",
                                                                                                      pady=(10, 0))
        ctk.CTkLabel(info, text=f"TL {value:.2f}", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w",
                                                                                                  pady=(0, 10))


if __name__ == "__main__":
    app = ExchangeApp()
    app.mainloop()
