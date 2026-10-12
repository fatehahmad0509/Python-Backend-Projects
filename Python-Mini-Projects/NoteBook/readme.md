📝 Notebook CLI App

A simple Python command-line notebook application that allows users to add, view, and delete notes stored in a local file.

🚀 Features
➕ Add new notes
👀 View all saved notes
🗑️ Delete notes by index
💾 Persistent storage using notes.txt
⚡ Lightweight and beginner-friendly CLI tool
🧠 How It Works

All notes are stored in a local file:

notes.txt

Each line represents one note.

When the program starts:

It loads existing notes into memory
Lets the user interact via a menu
Updates the file after changes
📦 Example Usage
---Welcome to the Notebook!

-Add Note: 1
-View Notes: 2
-Delete Note: 3
-Exit: 4
➕ Adding a note
Enter the note you want to add: Buy milk
Your note has been added successfully!
👀 Viewing notes
0 Buy milk
1 Study Python
🗑️ Deleting a note
Please enter the number of the note you wish to delete: 0
Note Successfully Deleted!
🛠️ Installation
1. Clone repo
git clone https://github.com/yourusername/notebook-cli.git
cd notebook-cli
2. Run program
python main.py
📁 Project Structure
notebook-cli/
│
├── main.py      # CLI application
├── notes.txt    # Stored notes (auto-created)
└── README.md
⚙️ Core Logic
💾 File Storage
append mode → adding notes
write mode → rewriting after deletion
🧠 In-memory list

Notes are also stored in a Python list (notebook) for quick operations.

⚠️ Notes
Input must be numeric in menu selection
Deleting invalid index will be safely handled
Notes are stored locally (no database)
🔮 Future Improvements
🔍 Search notes feature
🏷️ Categories / tags
🕒 Timestamp for each note
🔐 Password protection
☁️ Cloud sync version
🖥️ GUI upgrade (Tkinter / CustomTkinter)
👨‍💻 Author

A beginner-friendly CLI notebook app built with Python 🐍
Focused on file handling, loops, and basic CRUD logic ✍️
