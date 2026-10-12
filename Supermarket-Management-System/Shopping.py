import time
import sqlite3
import Products


def update_sql_item(product_obj):
    db = sqlite3.connect("saves.db")
    cursor = db.cursor()
    cursor.execute("UPDATE inventory SET price = ?, stock = ? WHERE id = ?",
                   (product_obj.price, product_obj.stock, product_obj.code))
    db.commit()
    db.close()


def startshopping():
    total_bill = 0
    shopping_list = [
        Products.bread, Products.milk, Products.egg, Products.rice, Products.pasta,
        Products.goudacheese, Products.stroopwafel, Products.organicmilk,
        Products.proteinbar, Products.water, Products.fruitjuice, Products.coffee,
        Products.frozenpizza, Products.sandwich, Products.microwavemeal,
        Products.detergent, Products.toiletpaper, Products.shampoo, Products.cocacola
    ]

    while True:
        try:
            print("\n--- SHOPPING MENU ---")
            product_number = int(input("Enter Product Number (1-19) or 0 to Finish: "))

            if product_number == 0:
                print(f"Total Bill: {total_bill} EUR")
                confirm_payment(total_bill)
                break

            selected = shopping_list[product_number - 1]

            if selected.stock > 0:
                selected.buy()
                total_bill += selected.price
                print(f"Added {selected.name}. Current Total: {total_bill} EUR")
            else:
                print(f"FAILED: {selected.name} is OUT OF STOCK!")

        except (ValueError, IndexError):
            print("Invalid input! Please enter a number between 1 and 19.")


def confirm_payment(total):
    choice = input("Confirm payment? (Y/N): ").upper()
    if choice == "Y":
        # UPDATE ALL CHANGED ITEMS TO SQL
        all_items = [
            Products.bread, Products.milk, Products.egg, Products.rice, Products.pasta,
            Products.goudacheese, Products.stroopwafel, Products.organicmilk,
            Products.proteinbar, Products.water, Products.fruitjuice, Products.coffee,
            Products.frozenpizza, Products.sandwich, Products.microwavemeal,
            Products.detergent, Products.toiletpaper, Products.shampoo, Products.cocacola
        ]
        for item in all_items:
            update_sql_item(item)

        print("Payment Successful! Database Updated.")
        time.sleep(2)
    else:
        print("Payment Cancelled.")

    import main
    main.mainmenu()