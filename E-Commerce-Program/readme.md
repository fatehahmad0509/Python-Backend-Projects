# 🛒 Ecommerce.com

A simple Python-based e-commerce application that includes user authentication, balance management, shopping cart functionality, stock tracking, and a modern Tkinter GUI.

## ✨ Features

### 🔐 User System

* User registration (Sign Up)
* User login (Password authentication)
* Account information storage using JSON files

### 💳 Balance Management

* Add money to account balance
* Withdraw money from account balance
* Persistent balance storage

### 🛍️ Shopping System

* Browse products
* Add products to cart
* Remove products from cart
* Change product quantities
* Checkout and payment system

### 📦 Inventory Management

* Product stock tracking
* Automatic stock reduction after purchase
* Out-of-stock protection
* Persistent stock storage

### 🧾 Receipt System

* Purchase summary
* Order receipt generation
* Remaining balance display

### 🎨 Modern GUI

* Dark theme design
* Product categories
* Search functionality
* Responsive layout
* Shopping cart interface

---

## 🛠️ Technologies Used

* Python 3
* Tkinter
* JSON
* Object-Oriented Programming (OOP)

---

## 📂 Project Structure

```text
project/
│
├── main.py
├── products.py
├── shopping.py
├── mainmenu.py
├── loginandsignup.py
│
├── accountinfos.json
├── balance.json
└── stocks.json
```

---

## 📋 Available Products

The application currently includes:

* Bread
* Milk
* Eggs
* Rice
* Pasta
* Gouda Cheese
* Stroopwafel
* Organic Milk
* Protein Bar
* Water
* Fruit Juice
* Coffee
* Frozen Pizza
* Sandwich
* Microwave Meal
* Detergent
* Toilet Paper
* Shampoo
* Coca Cola

---

## 🚀 Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/ecommerce-project.git
```

2. Enter the project directory:

```bash
cd ecommerce-project
```

3. Run the application:

```bash
python main.py
```

---

## 💾 Data Storage

The application stores data locally using JSON files:

| File              | Purpose                   |
| ----------------- | ------------------------- |
| accountinfos.json | User account information  |
| balance.json      | User balance              |
| stocks.json       | Product stocks and prices |

---

## 🎯 Future Improvements

* Multiple user accounts
* Admin panel
* Product images
* Database integration (SQLite/MySQL)
* Online payment simulation
* Order history
* Discount coupons
* User profile management

---

## 📄 License

This project is open source and available under the MIT License.

---

Made with ❤️ using Python.
