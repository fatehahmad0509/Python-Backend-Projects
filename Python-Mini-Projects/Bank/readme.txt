🏦 NF Bank – CLI Banking System (v1)

NF Bank is a command-line based banking simulation system built with Python.  
It allows users to create accounts, log in, and perform basic banking operations with persistent data storage.

---

## 🚀 Features

- Account registration system
- Login authentication
- Deposit & withdrawal system
- Balance inquiry
- Money transfer simulation
- Money request system (random approval logic)
- Persistent data storage using JSON & TXT files
- Email notification on account creation (SMTP)

---

## 🧠 How It Works

- User account information is stored in `accountinfos.json`
- Balance is stored in `balance.txt`
- User must register and log in before accessing the system
- Transactions update balance and are saved to file
- Email is sent automatically after registration

---

## 📁 Project Structure


nf-bank-cli-v1/
│
├── main.py
├── accountinfos.json
├── balance.txt
└── .env (email credentials)


---

## ▶️ How to Run

1. Install Python 3.x
2. Install dependencies:
```bash
pip install python-dotenv
Create .env file:
MAIL_USER=your_email
MAIL_PASS=your_password
Run the project:
python main.py
⚙️ Requirements

Built-in + external libraries:

json
time
random
smtplib
os
python-dotenv
💡 Learning Purpose

This project was built to practice:

File-based persistence (JSON & TXT)
User authentication system
Basic banking logic simulation
Email automation using SMTP
CLI application structure
Error handling and input validation
📈 Limitations (v1)
No password hashing (plain text storage)
No database integration
No transaction history log
Single user system only
Basic security model
🚀 Future Improvements (v2 idea)
Add SQLite database
Hash passwords (bcrypt)
Multi-user system
Transaction history
Better error handling system
GUI version (Tkinter / web app)
📬 Contact

📧 Email: fatehahmad503@gmail.com
💻 GitHub: https://github.com/fatehahmad0509

⭐ Thanks for checking out NF Bank v1!
