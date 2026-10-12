import sqlite3
import Products
from colorama import Fore
import time


def update_price_sql(product_obj):
    db = sqlite3.connect("saves.db")
    cursor = db.cursor()
    cursor.execute("UPDATE inventory SET price = ? WHERE id = ?", (product_obj.price, product_obj.code))
    db.commit()
    db.close()


def change_price():
    all_items = [Products.bread, Products.milk, Products.egg, Products.rice, Products.pasta,
                 Products.goudacheese, Products.stroopwafel, Products.organicmilk,
                 Products.proteinbar, Products.water, Products.fruitjuice, Products.coffee,
                 Products.frozenpizza, Products.sandwich, Products.microwavemeal,
                 Products.detergent, Products.toiletpaper, Products.shampoo, Products.cocacola]

    print("\n--- PRICE MANAGEMENT ---")
    for i, item in enumerate(all_items, 1):
        print(f"{i}: {item.name:<20} | Current: {item.price} EUR")

    try:
        choice = int(input("\nSelect product number (1-19): "))
        selected = all_items[choice - 1]
        new_price = float(input(f"Enter NEW price for {selected.name}: "))

        selected.price = new_price
        update_price_sql(selected)  # SAVE TO SQL
        print(f"SUCCESS: {selected.name} price updated to {new_price} EUR.")
    except:
        print("Update Failed!")

    time.sleep(2)
    import main
    main.mainmenu()