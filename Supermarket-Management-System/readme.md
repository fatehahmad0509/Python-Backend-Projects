Supermarket Management System (v3)

An advanced, modular Supermarket Management System built in Python, featuring dual-mode execution via a lightweight Command Line Interface (CLI) and a modern Graphical User Interface (GUI). Version 3 brings optimized performance, structured object-oriented data handling, persistent state management via local JSON databases, and automated administrative operations like dynamic restocking and bulk inflation application.

---

## 🚀 Features

* **Dual Interface Modality**: Run the system through an interactive terminal environment (`main.py`) or spin up a sleek, windowed Desktop application built with CustomTkinter (`marketgui.py`).
* **Dynamic Inventory Processing**: Real-time stock decrement sequences execute automatically during checkout, alongside immediate user interface refreshes.
* **State Persistence**: Complete structural integrity for pricing metrics and current stock tiers is managed dynamically using a serialized `stocks.json` storage file.
* **Administrative Operations Control**: A dedicated, passcode-protected (`1234`) Admin Console allows store managers to apply global macros, including automated +10% bulk inflation updates and full inventory replenishments.
* **Formatted Terminal UX**: Employs `colorama` ANSI escape sequences within the CLI runtime to deliver readable, distinct validation logs and step-by-step transaction details.

---

## 📁 Project Structure

```text
SupermarketManagementSystem (v3)/
│
├── Products.py          # OOP structure mapping database blueprints and asset configurations
├── main.py              # CLI runtime controller and primary terminal routing grid
├── marketgui.py         # Advanced graphical dashboard powered by the CustomTkinter engine
│
├── Shopping.py          # Business logic managing checkout operations, receipt production, and user carts
├── StockControl.py      # Inventory query engine reading directly from serialized local storage
├── changestock.py       # Admin service module to provision, override, or increment item quantities
└── changeprice.py       # Admin utility enabling targeted or global baseline price modifications
🛠️ Installation & Requirements
The ecosystem requires Python 3.8 or greater. Install the dependencies via pip:


pip install customtkinter colorama
💻 Running the Application
1. Graphical Mode (GUI)
To initialize the responsive visual control center, run:


python marketgui.py
Note: Enter the default administrative passcode 1234 in the top right to access management overrides.

2. Terminal Mode (CLI)
To initialize the streamlined console menu structure, run:


python main.py
⚙️ Core Catalog Structure
The system tracks and processes 19 essential commodities structured into production sectors:

Pantry & Fresh Goods: Bread, Milk, Eggs, Rice, Pasta, Gouda Cheese, Stroopwafel, Organic Milk, Protein Bar, Frozen Pizza, Sandwich, Microwave Meal, Coca-Cola.

Beverages: Water, Juice, Coffee.

Sanitation & Hygiene: Detergent, Toilet Paper, Shampoo.
