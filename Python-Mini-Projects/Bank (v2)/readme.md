🏦 NF Bank – Python Banking System (CLI + GUI)

NF Bank is a simulated banking system built with Python.  
It includes both a **command-line version** and a **GUI-based desktop application** using Tkinter.

---

## 🚀 Features

### 💻 GUI Version (Tkinter)
- User registration system
- Login authentication
- Account balance dashboard
- Deposit / Withdrawal
- Wire transfers (simulated)
- Money request system (random approval)
- Secure credential storage (JSON)
- Email notification on registration (SMTP)

### 🖥️ CLI Version
- Deposit & withdrawal system
- Balance tracking with file storage
- Send / request money simulation
- Login system
- Account creation system
- Email welcome system

---

## 🧠 How It Works

- User data is stored in `accountinfos.json`
- Balance is stored in `balance.txt`
- Email system uses Gmail SMTP
- GUI is built using Tkinter
- CLI uses file-based persistence

---

## 📁 Project Structure


NF-Bank/
│
├── gui_version.py
├── cli_version.py
├── accountinfos.json
├── balance.txt
└── .env (email credentials)


---

## ▶️ How to Run

### GUI Version
```bash
python gui_version.py
CLI Version
python cli_version.py
⚙️ Requirements

Built-in + external:

tkinter
json
random
smtplib
python-dotenv

Install dotenv:

pip install python-dotenv
🔐 Security Note

This project uses .env file to store email credentials securely:

MAIL_USER=your_email
MAIL_PASS=your_password
💡 Learning Purpose

This project was built to practice:

GUI development (Tkinter)
File handling (JSON + TXT)
Authentication systems
Email automation (SMTP)
Modular Python programming
CLI + GUI architecture
📈 Future Improvements
Database integration (SQLite / PostgreSQL)
Better encryption for passwords
Multi-user account system
Transaction history log
Modern UI redesign (customtkinter / web app)
📬 Contact

📧 Email: fatehahmad503@gmail.com
💻 GitHub: https://github.com/fatehahmad0509
