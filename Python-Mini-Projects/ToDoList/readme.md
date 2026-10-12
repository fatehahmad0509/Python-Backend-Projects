📝 ToDo List Desktop App

A modern desktop ToDo List application built with Python, featuring a sleek UI using CustomTkinter and persistent storage with SQLite.

🚀 Features
➕ Add new notes instantly
🗑️ Delete notes with one click
💾 Persistent storage using SQLite database
🎨 Modern dark-themed UI
⚡ Smooth and responsive interface
📊 Live note counter
⌨️ Enter key support for fast input
🧠 Tech Stack
Python 🐍
CustomTkinter (modern UI framework)
Tkinter (base GUI)
SQLite3 (local database)
📦 Installation
1. Clone the repository
git clone https://github.com/your-username/todo-list-app.git
cd todo-list-app
2. Install dependencies
pip install customtkinter
3. Run the application
python main.py
🗄️ Database

The application automatically creates a local SQLite database:

notes.db
Table structure:
CREATE TABLE notes (
    note TEXT
)
🎨 UI Overview
Dark minimalist theme
Smooth hover effects
Custom animated components (CustomTkinter)
Clean note cards with delete buttons
Responsive scrollable layout
⚙️ Project Structure
project/
│
├── main.py        # UI (CustomTkinter frontend)
├── backend.py     # SQLite database logic
└── notes.db       # Auto-generated database
🧠 How It Works
User adds a note via UI
Note is saved to SQLite database
UI dynamically updates without reload
Deleting removes from both UI and DB
⚡ Future Improvements
✏️ Edit notes feature
🔍 Search bar for notes
📁 Categories / tags
☁️ Cloud sync support
🔔 Reminder system
📱 Mobile version (Kivy / web app)
👨‍💻 Developer Notes

This project demonstrates:

GUI development with Python
Local database integration
Clean UI/UX design principles
Event-driven programming
📸 Preview

(Add screenshots here for better GitHub presentation)

⭐ If you like this project

Give it a ⭐ on GitHub — it really helps motivation 😄🔥
