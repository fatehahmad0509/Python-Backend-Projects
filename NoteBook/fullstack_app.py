import tkinter as tk
from tkinter import messagebox

class ModernNotebook:
    def __init__(self, root):
        self.root = root
        self.root.title("Notebook")
        self.root.geometry("400x550")
        self.root.configure(bg="#121212")

        self.notes = []
        self.load_notes()

        self.header = tk.Label(
            root, text="My Notes", font=("Inter", 22, "bold"),
            bg="#121212", fg="#FFFFFF"
        )
        self.header.pack(pady=(30, 20))

        self.input_frame = tk.Frame(root, bg="#1E1E1E", padx=10, pady=10)
        self.input_frame.pack(padx=20, fill="x")

        self.entry = tk.Entry(
            self.input_frame, font=("Inter", 11), bg="#1E1E1E",
            fg="#FFFFFF", borderwidth=0, insertbackground="#FFFFFF"
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=5)
        self.entry.bind("<Return>", lambda e: self.add_note())

        self.add_btn = tk.Button(
            self.input_frame, text="ADD", command=self.add_note,
            bg="#BB86FC", fg="#000000", font=("Inter", 9, "bold"),
            relief="flat", padx=15, pady=5, cursor="hand2"
        )
        self.add_btn.pack(side="right")

        self.list_frame = tk.Frame(root, bg="#121212")
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.listbox = tk.Listbox(
            self.list_frame, font=("Inter", 11), bg="#1E1E1E",
            fg="#E0E0E0", borderwidth=0, highlightthickness=0,
            selectbackground="#333333", activestyle="none"
        )
        self.listbox.pack(side="left", fill="both", expand=True)

        self.scrollbar = tk.Scrollbar(self.list_frame, command=self.listbox.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=self.scrollbar.set)

        self.delete_btn = tk.Button(
            root, text="DELETE SELECTED", command=self.delete_note,
            bg="#CF6679", fg="#000000", font=("Inter", 10, "bold"),
            relief="flat", pady=12, cursor="hand2"
        )
        self.delete_btn.pack(fill="x", padx=20, pady=(0, 30))

        self.refresh_list()

    def load_notes(self):
        try:
            with open("notes.txt", "r", encoding="utf-8") as f:
                self.notes = [line.strip() for line in f.readlines()]
        except FileNotFoundError:
            self.notes = []

    def save_notes(self):
        with open("notes.txt", "w", encoding="utf-8") as f:
            for note in self.notes:
                f.write(note + "\n")

    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        for note in self.notes:
            self.listbox.insert(tk.END, note)

    def add_note(self):
        content = self.entry.get().strip()
        if content:
            self.notes.append(content)
            self.save_notes()
            self.refresh_list()
            self.entry.delete(0, tk.END)

    def delete_note(self):
        try:
            index = self.listbox.curselection()[0]
            del self.notes[index]
            self.save_notes()
            self.refresh_list()
        except IndexError:
            pass

if __name__ == "__main__":
    app_root = tk.Tk()
    app = ModernNotebook(app_root)
    app_root.mainloop()