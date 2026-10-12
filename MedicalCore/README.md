🏥 MedicalCore – Hospital Management System

A modern Python + PostgreSQL + CustomTkinter based hospital management system with role-based access for doctors and staff.

It includes appointment handling, patient registration, doctor management, and diagnosis tracking in a single desktop application.

🚀 Features
🔐 Authentication System
👨‍⚕️ Doctor login (ID-based)
🧑‍💼 Staff login (name + password)
📅 Appointment Management
Create new appointments
Assign doctors to patients
Track appointment status:
Waiting
In Progress
Completed
Cancelled
👨‍⚕️ Doctor Panel
View personal appointments
Add diagnosis & medical notes
Update appointment status
Mark appointments as completed
🧑‍💼 Staff Panel
Register new patients
Create appointments
Add & delete doctors
View all appointments in table form
Cancel appointments
🧠 Tech Stack
🐍 Python
🖼️ CustomTkinter (Modern GUI)
🗄️ PostgreSQL (via psycopg2)
🌐 dotenv (.env config support)
🧵 Threading (non-blocking UI)
📦 Tkinter Treeview (data tables)
🗃️ Database Schema
Doctors Table
doctor_id INTEGER PRIMARY KEY,
full_name TEXT,
birthdate DATE,
id_no TEXT
Staffs Table
staff_id INTEGER PRIMARY KEY,
full_name TEXT,
password TEXT,
id_no TEXT
Appointments Table
appointment_id SERIAL PRIMARY KEY,
full_name VARCHAR,
doctor_id INTEGER REFERENCES doctors,
date DATE,
time TIME,
id_no VARCHAR(11),
phone VARCHAR,
gender VARCHAR,
blood_type VARCHAR,
birth_date DATE,
medical_history TEXT,
status VARCHAR CHECK (status IN ('waiting','in_progress','completed','cancelled'))
⚙️ Installation
1. Clone repository
git clone https://github.com/yourusername/medicalcore.git
cd medicalcore
2. Install dependencies
pip install customtkinter psycopg2 python-dotenv
🔑 Environment Setup

Create a .env file:

DATABASE_URL=postgresql://username:password@localhost:5432/your_database
▶️ Run Application
python main.py
🖥️ UI Overview
🧑 Login screen (Doctor / Staff switch)
📊 Dashboard with statistics
📅 Appointment table (filterable)
🏥 Patient registration form
👨‍⚕️ Doctor management panel
📄 Diagnosis / medical notes popup
🔥 Key Features Explained
🧵 Threaded Database Calls

UI never freezes because all DB operations run in background threads.

📊 Real-time Status System

Appointments dynamically update:

Badge colors
Filtered views
Dashboard stats
🏥 Role-Based System
Doctors: manage patients & notes
Staff: manage hospital data
⚠️ Notes
Requires PostgreSQL running locally or remote
Internet check is enforced at startup
.env file is required
No password hashing (can be improved 🔐)
🚀 Future Improvements
🔐 Password hashing (bcrypt)
🌍 Web version (FastAPI + React)
📱 Mobile app version
📈 Analytics dashboard
🧠 AI diagnosis suggestion system
☁️ Cloud deployment
👨‍💻 Author

Built with ❤️ using Python
A full-stack desktop hospital system simulation with real database integration 🏥💻
