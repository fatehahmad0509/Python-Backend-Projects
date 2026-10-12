import sqlite3
import time


def stockcontrol():
    print(Fore.YELLOW + "\n--- LIVE STOCK STATUS ---")
    try:
        db = sqlite3.connect("saves.db")
        cursor = db.cursor()

        # SQL query to get name and stock
        cursor.execute("SELECT name, stock FROM inventory")
        rows = cursor.fetchall()

        # Table header
        print(f"{'Product Name':<20} | {'Stock Amount':<10}")
        print("-" * 35)

        for row in rows:
            name, stock = row
            # If stock is low, show in RED (optional trick)
            print(f"{name:<20} | {stock:<10} units")

        db.close()
    except sqlite3.Error as e:
        print(f"Database error: {e}")

    input("\nPress Enter to return to main menu...")
    import main
    main.mainmenu()


if __name__ == "__main__":
    from colorama import Fore  # If running standalone

    stockcontrol()