import tkinter as tk
from tkinter import messagebox, simpledialog
import json
import random
import smtplib
from email.message import EmailMessage
import threading
import os
from dotenv import load_dotenv


load_dotenv()

EMAIL_ADDRESS = os.getenv("MAIL_USER")
EMAIL_PASSWORD = os.getenv("MAIL_PASS")

class NFBankApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NF BANK | PREMIER ACCESS")
        self.root.geometry("450x800")
        self.root.configure(bg="#020617")

        self.color_bg = "#020617"
        self.color_card = "#1e293b"
        self.color_gold = "#fbbf24"
        self.color_white = "#f8fafc"
        self.color_blue = "#38bdf8"

        self.balance_file = "balance.txt"
        self.account_file = "accountinfos.json"
        self.current_balance = self.load_balance()
        self.account_info = self.load_account_info()

        self.main_frame = tk.Frame(self.root, bg=self.color_bg)
        self.main_frame.pack(expand=True, fill="both")

        if not self.account_info:
            self.show_register_screen()
        else:
            self.show_login_screen()

    def load_balance(self):
        if os.path.exists(self.balance_file):
            with open(self.balance_file, "r") as f:
                try:
                    return int(f.read().strip())
                except:
                    return 0
        return 0

    def save_balance(self):
        with open(self.balance_file, "w") as f:
            f.write(str(self.current_balance))

    def load_account_info(self):
        if os.path.exists(self.account_file):
            with open(self.account_file, "r") as f:
                return json.load(f)
        return None

    def send_welcome_email_async(self, to_email, name):
        def send():
            try:
                msg = EmailMessage()
                msg['Subject'] = "Welcome to NF Bank!"
                msg['From'] = "welcome.nfbank@gmail.com"
                msg['To'] = to_email
                msg.set_content(
                    f"Hi {name}, Your NF Bank account has been successfully created! Welcome to the world of private banking.")

                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                    smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                    smtp.send_message(msg)
            except Exception as e:
                print(f"Email could not be sent: {e}")

        threading.Thread(target=send).start()

    def clear_screen(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_register_screen(self):
        self.clear_screen()
        tk.Label(self.main_frame, text="NF PRIVATE", font=("Arial", 24, "bold"), fg=self.color_gold,
                 bg=self.color_bg).pack(pady=(40, 20))

        container = tk.Frame(self.main_frame, bg=self.color_bg)
        container.pack(padx=50, fill="x")

        fields = [
            ("FULL NAME", "name"),
            ("AGE", "age"),
            ("BIRTH DATE (DD/MM/YYYY)", "bd"),
            ("EMAIL ADDRESS", "email"),
            ("PASSWORD", "pass")
        ]
        self.entries = {}

        for label_text, key in fields:
            tk.Label(container, text=label_text, font=("Arial", 8, "bold"), fg=self.color_blue, bg=self.color_bg).pack(
                anchor="w")
            is_pass = True if key == "pass" else False
            ent = tk.Entry(container, show="*" if is_pass else "", font=("Arial", 11), bg="#0f172a", fg="white", bd=0,
                           highlightthickness=1, highlightbackground="#334155")
            ent.pack(fill="x", pady=(2, 12), ipady=8)
            self.entries[key] = ent

        def register():
            try:
                name = self.entries["name"].get()
                age_str = self.entries["age"].get()
                bd = self.entries["bd"].get()
                email = self.entries["email"].get()
                password = self.entries["pass"].get()

                if not all([name, age_str, bd, email, password]):
                    messagebox.showerror("ERROR", "Please fill all fields.")
                    return

                age = int(age_str)
                if age < 18:
                    messagebox.showwarning("NOTICE", "Private banking requires 18+ years.")
                    return

                user_data = {
                    "fullname": name,
                    "age": age,
                    "birthdate": bd,
                    "email": email,
                    "password": password
                }

                with open(self.account_file, "w") as f:
                    json.dump(user_data, f)
                self.account_info = user_data

                self.send_welcome_email_async(email, name)

                messagebox.showinfo("SUCCESS", "Account created! A welcome email is being sent.")
                self.show_login_screen()
            except ValueError:
                messagebox.showerror("ERROR", "Age must be a number.")

        tk.Button(self.main_frame, text="CREATE PROFILE", command=register, font=("Arial", 10, "bold"),
                  bg=self.color_gold, fg="black", bd=0, cursor="hand2").pack(pady=20, padx=50, fill="x", ipady=12)

    def show_login_screen(self):
        self.clear_screen()
        tk.Label(self.main_frame, text="NF BANK", font=("Arial", 28, "bold"), fg=self.color_gold,
                 bg=self.color_bg).pack(pady=(120, 10))
        tk.Label(self.main_frame, text="SECURE ACCESS", font=("Arial", 10), fg=self.color_blue, bg=self.color_bg).pack(
            pady=(0, 40))

        pass_ent = tk.Entry(self.main_frame, show="*", font=("Arial", 16), bg="#0f172a", fg="white", bd=0,
                            justify="center", highlightthickness=1, highlightbackground="#334155")
        pass_ent.pack(pady=20, padx=80, fill="x", ipady=12)

        def login_check():
            if pass_ent.get() == self.account_info['password']:
                self.show_main_menu()
            else:
                messagebox.showerror("FAILED", "Authentication failed.")

        tk.Button(self.main_frame, text="AUTHORIZE", command=login_check, font=("Arial", 10, "bold"),
                  bg=self.color_gold, fg="black", bd=0).pack(pady=10, padx=80, fill="x", ipady=12)

    def show_main_menu(self):
        self.clear_screen()

        card = tk.Frame(self.main_frame, bg=self.color_card, padx=25, pady=25, highlightthickness=1,
                        highlightbackground=self.color_gold)
        card.pack(pady=40, padx=30, fill="x")

        tk.Label(card, text="NF PRIVATE CLIENT", font=("Arial", 9, "bold"), fg=self.color_gold,
                 bg=self.color_card).pack(anchor="w")
        tk.Label(card, text="**** **** **** 8842", font=("Courier", 14), fg=self.color_white, bg=self.color_card).pack(
            anchor="w", pady=20)

        tk.Label(card, text="TOTAL LIQUIDITY", font=("Arial", 8), fg=self.color_blue, bg=self.color_card).pack(
            anchor="w")
        self.balance_label = tk.Label(card, text=f"$ {self.current_balance:,.2f}", font=("Arial", 24, "bold"),
                                      fg=self.color_white, bg=self.color_card)
        self.balance_label.pack(anchor="w")

        ops_frame = tk.Frame(self.main_frame, bg=self.color_bg)
        ops_frame.pack(fill="x", padx=40)

        menu = [
            ("DEPOSIT", self.deposit_ui),
            ("WITHDRAWAL", self.withdraw_ui),
            ("WIRE TRANSFER", self.send_money_ui),
            ("REQUEST ASSETS", self.request_money_ui),
            ("LOGOUT", self.root.quit)
        ]

        for text, func in menu:
            btn = tk.Button(ops_frame, text=text, command=func, font=("Arial", 9, "bold"), bg="#0f172a",
                            fg=self.color_white, bd=0, anchor="w", padx=20)
            btn.pack(fill="x", pady=4, ipady=12)
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=self.color_card, fg=self.color_gold))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg="#0f172a", fg=self.color_white))

    def update_ui(self):
        self.balance_label.config(text=f"$ {self.current_balance:,.2f}")
        self.save_balance()

    def deposit_ui(self):
        val = simpledialog.askinteger("TRANSACTION", "Amount to deposit:", parent=self.root)
        if val and val > 0:
            self.current_balance += val
            self.update_ui()

    def withdraw_ui(self):
        val = simpledialog.askinteger("TRANSACTION", "Amount to withdraw:", parent=self.root)
        if val:
            if val <= self.current_balance:
                self.current_balance -= val
                self.update_ui()
            else:
                messagebox.showwarning("NOTICE", "Insufficient funds.")

    def send_money_ui(self):
        iban = simpledialog.askstring("TRANSFER", "Target IBAN Number:", parent=self.root)
        if iban:
            val = simpledialog.askinteger("TRANSFER", "Transaction Amount:", parent=self.root)
            if val and val <= self.current_balance:
                self.current_balance -= val
                self.update_ui()
                messagebox.showinfo("SENT", f"Transfer to {iban} successful.")

    def request_money_ui(self):
        iban = simpledialog.askstring("REQUEST", "Enter Sender IBAN:", parent=self.root)
        if iban:
            val = simpledialog.askinteger("REQUEST", "Requested Amount:", parent=self.root)
            if val and val > 0:
                if random.choice([True, False]):
                    self.current_balance += val
                    self.update_ui()
                    messagebox.showinfo("APPROVED", "The request was approved.")
                else:
                    messagebox.showwarning("DECLINED", "The request was rejected.")


if __name__ == "__main__":
    root = tk.Tk()
    app = NFBankApp(root)
    root.mainloop()