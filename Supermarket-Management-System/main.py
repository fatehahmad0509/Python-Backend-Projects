import time
import sqlite3
import Products
from colorama import Fore, init

# Colorama'yı başlat (Windows'ta renklerin düzgün gözükmesi için)
init(autoreset=True)


def load_inventory():
    db = sqlite3.connect("saves.db")
    cursor = db.cursor()

    # 1. Tabloyu "inventory" adıyla oluşturuyoruz
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

    # 2. KRİTİK DÜZELTME: Burası "saves" değil "inventory" olmalıydı
    cursor.execute("SELECT count(*) FROM inventory")

    if cursor.fetchone()[0] == 0:
        print(Fore.YELLOW + "Initializing database with default products...")
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

    # 3. Verileri SQL'den Python objelerine yükle
    cursor.execute("SELECT name, price, stock FROM inventory")
    rows = cursor.fetchall()

    for row in rows:
        name, price, stock = row
        # İsim eşleştirme (Örn: "Milk (1L)" -> "milk")
        var_name = name.lower().split()[0].replace("(", "")
        if hasattr(Products, var_name):
            item = getattr(Products, var_name)
            item.price = price
            item.stock = stock
            item.instock = stock > 0

    db.close()


def adminpanel():
    print(Fore.RED + "\n--- Admin Panel ---")
    print("1. Change Stock")
    print("2. Change Price")
    print("3. Back to Main Menu")
    try:
        choice = int(input("Enter Process: "))
        if choice == 1:
            import changestock
            changestock.change_stock()
        elif choice == 2:
            import changeprice
            changeprice.change_price()
        elif choice == 3:
            mainmenu()
    except:
        print("Invalid input, returning to Admin Panel...")
        adminpanel()


def mainmenu():
    # Menü her açıldığında SQL ile Python objelerini senkronize et
    load_inventory()
    print(Fore.CYAN + "\n=== SHOP MANAGEMENT SYSTEM ===")
    print("1: Shopping")
    print("2: Stock Control")
    print("3: Admin Panel")
    print("4: Exit")

    try:
        process = int(input("Select: "))
        if process == 1:
            import Shopping
            Shopping.startshopping()
        elif process == 2:
            import StockControl
            StockControl.stockcontrol()
        elif process == 3:
            adminpanel()
        elif process == 4:
            print("Exiting system...")
            exit()
        else:
            print("Please enter a valid number (1-4)")
            mainmenu()
    except ValueError:
        print("Please enter a number!")
        mainmenu()


if __name__ == "__main__":
    mainmenu()