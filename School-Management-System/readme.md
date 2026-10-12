🏫 School Management System

A modern Python-based School Management System with a graphical user interface.
It supports student and teacher roles, grade management, and persistent data storage using PostgreSQL.

🚀 Features
👨‍🎓 Student Panel
View personal profile
Check grades (exams, performance, average, status)
View classmates
Change password
👨‍🏫 Teacher Panel
View students by class
Add and update grades
Generate student reports (average & pass/fail status)
Remove students
Manage subject-based grading
🧠 Technologies Used
Python 🐍
Tkinter (GUI)
PostgreSQL 🗄️
psycopg2
python-dotenv (.env support)
hashlib (password hashing)
threading (non-blocking UI)
📦 Installation
1. Clone the repository
git clone https://github.com/your-username/school-management-system.git
cd school-management-system
2. Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
3. Install dependencies
pip install -r requirements.txt
4. Create a .env file

Add the following environment variable:

DATABASE_URL=postgresql://username:password@localhost:5432/database_name
5. Run the application
python main.py
🗄️ Database Structure

The system automatically creates the following tables:

students
teachers
grades
logs
🔐 Security
Passwords are hashed using SHA-256
Role-based authentication (student / teacher)
Parameterized SQL queries to prevent injection attacks
📊 Architecture
UI (Tkinter)
   ↓
Business Logic (Python)
   ↓
Database Layer (PostgreSQL)
⚡ Highlights
Modern dark-themed UI 🎨
Threaded backend (no UI freezing)
Role-based authentication system
Real-time grade management
🛠️ Future Improvements
Admin dashboard
Data visualization for student performance 📈
REST API integration (FastAPI)
Web version (React + backend API)
Docker support
👨‍💻 Developer

This project was built as a learning-focused full-featured desktop application using Python.
