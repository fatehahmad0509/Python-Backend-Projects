📝 Modern Notebook

A simple Python note-taking application with both:

🖥️ Modern GUI version (Tkinter)
💻 Console-based CLI version

Notes are stored locally in a notes.txt file and persist between sessions.

🚀 Features
🖼️ GUI Version (ModernNotebook)
🌙 Dark-themed modern interface
➕ Add notes instantly
🗑️ Delete selected notes
💾 Auto-save to file
📜 Scrollable notes list
⌨️ Enter key support for quick adding
💻 CLI Version
📋 Add notes via terminal
👀 View all saved notes
❌ Delete notes by index
💾 File-based storage system
🧠 How It Works

All notes are stored in:

notes.txt

Each line represents one note.

🖥️ GUI Preview

Built using:

tkinter
Listbox + Scrollbar
Custom styled widgets (dark mode UI)
📦 Installation
1. Clone repo
git clone https://github.com/yourusername/modern-notebook.git
cd modern-notebook
2. Run GUI version
python gui.py
3. Run CLI version
python cli.py
📁 Project Structure
modern-notebook/
│
├── gui.py        # Tkinter GUI version
├── cli.py        # Command-line version
├── notes.txt     # Stored notes (auto-generated)
└── README.md
⚙️ Core Features Explained
💾 Persistent Storage

Notes are saved in a local file using simple file I/O:

append mode → adding notes
write mode → deleting/updating notes
🧾 Dual Interface Design

Same functionality implemented in two ways:

GUI for usability
CLI for simplicity & learning
🧠 Error Handling
Handles empty inputs
Prevents invalid deletions
Graceful file loading (FileNotFoundError safe)
⚠️ Notes
Notes are stored locally (no cloud sync)
No encryption or user accounts
Designed for learning file handling + GUI basics
🔮 Future Improvements
☁️ Cloud sync (Firebase / Supabase)
🔐 Password-protected notes
🏷️ Tags & categories
🔍 Search system
🎨 Better UI (CustomTkinter upgrade)
📱 Mobile version
👨‍💻 Author

A beginner-friendly dual-mode notebook app built with Python 🐍
Focused on file handling, GUI design, and basic CRUD operations ✍️
