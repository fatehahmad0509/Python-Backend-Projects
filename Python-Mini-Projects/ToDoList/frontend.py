import tkinter as tk
import customtkinter as ctk
from backend import to_do_list

BG = "#0F0F0F"
SURFACE = "#1A1A1A"
BORDER = "#2A2A2A"
ACCENT = "#C9A96E"
ACCENT_DIM = "#5C4A2A"
TEXT = "#F0EDE8"
TEXT_MUTED = "#6B6760"
DANGER = "#8B3A3A"

FONT_TITLE = ("Georgia", 26)
FONT_BODY = ("Helvetica Neue", 13)
FONT_SUB = ("Helvetica Neue", 11)


class NoteItem(ctk.CTkFrame):
    def __init__(self, master, text, delete_command):
        super().__init__(master, fg_color=SURFACE, corner_radius=0)
        self.note_text = text

        self.main_container = ctk.CTkFrame(self, fg_color="transparent", height=52, corner_radius=0)
        self.main_container.pack(side="top", fill="x")
        self.main_container.pack_propagate(False)

        self.label = ctk.CTkLabel(
            self.main_container, text=text, text_color=TEXT,
            font=ctk.CTkFont(family="Helvetica Neue", size=13),
            anchor="w"
        )
        self.label.pack(side="left", padx=(20, 10), expand=True, fill="both")

        self.del_btn = ctk.CTkButton(
            self.main_container, text="✕", width=26, height=26,
            fg_color="transparent", text_color=TEXT_MUTED,
            hover_color=DANGER, corner_radius=4,
            command=lambda: delete_command(self.note_text)
        )
        self.del_btn.pack(side="right", padx=16)

        self.line = ctk.CTkFrame(self, fg_color=BORDER, height=2, corner_radius=0)
        self.line.pack(side="bottom", fill="x")

        for widget in [self.main_container, self.label]:
            widget.bind("<Enter>", self.on_enter)
            widget.bind("<Leave>", self.on_leave)

    def on_enter(self, event):
        self.main_container.configure(fg_color="#1F1F1F")
        self.del_btn.configure(text_color=TEXT)

    def on_leave(self, event):
        self.main_container.configure(fg_color="transparent")
        self.del_btn.configure(text_color=TEXT_MUTED)

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.todo = to_do_list()
        self.note_widgets = {}

        self.title("ToDoList")
        self.geometry("520x700")
        self.configure(fg_color=BG)

        self._build_ui()
        self._load_notes()

    def _build_ui(self):
        self.header = ctk.CTkFrame(self, fg_color=BG, height=120, corner_radius=0)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)

        title_lbl = ctk.CTkLabel(self.header, text="ToDoList", text_color=TEXT, font=FONT_TITLE)
        title_lbl.pack(anchor="w", padx=28, pady=(24, 0))

        self.subtitle = ctk.CTkLabel(self.header, text="0 notes", text_color=TEXT_MUTED, font=FONT_SUB)
        self.subtitle.pack(anchor="w", padx=28)

        self.input_bar = ctk.CTkFrame(self, fg_color=SURFACE, height=64, corner_radius=0, border_width=1,
                                      border_color=BORDER)
        self.input_bar.pack(fill="x")
        self.input_bar.pack_propagate(False)

        self.entry = ctk.CTkEntry(
            self.input_bar, placeholder_text="Add a new note...",
            fg_color="transparent", border_width=0, text_color=TEXT,
            font=FONT_BODY, placeholder_text_color=TEXT_MUTED
        )
        self.entry.pack(side="left", padx=(20, 10), expand=True, fill="both")
        self.entry.bind("<Return>", lambda e: self.add_note())

        add_btn = ctk.CTkButton(
            self.input_bar, text="+ Add", width=76, height=36,
            fg_color=ACCENT, hover_color="#D4B07A", text_color=BG,
            font=ctk.CTkFont(family="Helvetica Neue", size=11, weight="bold"),
            command=self.add_note
        )
        add_btn.pack(side="right", padx=16)

        self.scroll_canvas = ctk.CTkScrollableFrame(
            self, fg_color=BG, corner_radius=0,
            orientation="vertical",
            label_text="",
        )
        self.scroll_canvas.pack(fill="both", expand=True)
        self.scroll_canvas._scrollbar.configure(width=4)

        self.empty_label = ctk.CTkLabel(
            self.scroll_canvas, text="No notes yet.\nAdd one above.",
            text_color=TEXT_MUTED, font=FONT_BODY
        )
        self.empty_label.pack(pady=60)

    def _load_notes(self):
        for (text,) in self.todo.view_notes():
            self._add_widget(text)
        self._update_subtitle()

    def _add_widget(self, text: str):
        if self.empty_label:
            self.empty_label.pack_forget()

        item = NoteItem(self.scroll_canvas, text, self.delete_note)
        item.pack(fill="x")
        self.note_widgets[text] = item

    def _update_subtitle(self):
        total = len(self.note_widgets)
        self.subtitle.configure(text=f"{total} note{'s' if total != 1 else ''}")

    def add_note(self):
        text = self.entry.get().strip()
        if not text:
            self._show_error("Note cannot be empty.")
            return
        if text in self.note_widgets:
            self._show_error("This note already exists.")
            return

        self.todo.add_note(text)
        self._add_widget(text)
        self.entry.delete(0, tk.END)
        self._update_subtitle()

    def delete_note(self, text: str):
        self.todo.delete_note(text)
        if text in self.note_widgets:
            self.note_widgets[text].destroy()
            del self.note_widgets[text]

        if not self.note_widgets:
            self.empty_label.pack(pady=60)
        self._update_subtitle()

    def _show_error(self, msg: str):
        print(f"Error: {msg}")


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()