🏦 ATM Simulation (Python CLI) — Version 1

This project is a simple ATM simulation built using Python.  
It simulates basic banking operations in a command-line interface and stores user balance in a local file.

---

## 🚀 Features

- Deposit money  
- Withdraw money  
- Check balance  
- Send money (simulated transfer)  
- Request money (random approval system)  
- Persistent balance storage using `balance.txt`

---

## 🧠 How It Works

The program loads the user's balance from a local file (`balance.txt`).  
If the file does not exist, the balance starts at 0.

All transactions update the balance and save it back to the file automatically.

The "Request Money" feature simulates real-world uncertainty using random outcomes.

---

## 📁 Project Structure


atm-v1/
│
├── main.py
├── balance.txt (auto-generated)
└── README.md


---

## ▶️ How to Run

1. Install Python 3.x
2. Run the script:

```bash
python main.py
⚙️ Requirements

This project uses only built-in Python modules:

time
random

No external libraries are required.

💡 What I Learned

This project helped me practice:

File handling in Python
Functions and program structure
Error handling with try/except
Loop and menu system design
Basic simulation logic
📈 Future Improvements (v2)
Add user authentication (PIN system)
Improve code structure (OOP version)
Add transaction history
Support multiple users/accounts
Better UI/UX flow
📬 Contact

For questions or feedback:
📧 fatehahmad0509@gmail.com

⭐ Thanks for checking out this project!
