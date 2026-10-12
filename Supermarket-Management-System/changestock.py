import sqlite3
import Products
import time


def update_stock_sql(product_obj):
    db = sqlite3.connect("saves.db")
    cursor = db.cursor()
    cursor.execute("UPDATE inventory SET stock = ? WHERE id = ?", (product_obj.stock, product_obj.code))
    db.commit()
    db.close()


def change_stock():
    all_items = [Products.bread, Products.milk, Products.egg, Products.rice, Products.pasta,
                 Products.goudacheese, Products.stroopwafel, Products.organicmilk,
                 Products.proteinbar, Products.water, Products.fruitjuice, Products.coffee,
                 Products.frozenpizza, Products.sandwich, Products.microwavemeal,
                 Products.detergent, Products.toiletpaper, Products.shampoo, Products.cocacola]

    try:
        choice = int(input("Select product number to update stock: "))
        selected = all_items[choice - 1]
        amount = int(input(f"Current: {selected.stock}. Enter amount to ADD (use - for remove): "))

        selected.stock += amount
        if selected.stock < 0: selected.stock = 0

        update_stock_sql(selected)  # SAVE TO SQL
        print(f"SUCCESS: {selected.name} stock is now {selected.stock}!")
    except:
        print("Error during update.")

    time.sleep(2)
    import main
    main.mainmenu()