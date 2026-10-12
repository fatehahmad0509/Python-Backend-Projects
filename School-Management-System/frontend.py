import tkinter as tk
from tkinter import ttk, messagebox, font
import sys
import os
import threading
import socket

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend import (
    create_tables,
    signupasstudent,
    signupasteacher,
    loginasteacher,
    loginasstudent,
    generate_student_number,
    getstudentsbyclass,
    updategrade,
    deletestudent,
    getstudentreports,
    addgrade,
    getstudentprofile,
    changepassword,
    getclassmates,
    getmygrades,
)

PRIMARY       = "#0A0F1E"
SECONDARY     = "#0D1B2A"
PANEL         = "#111827"
CARD          = "#1A2235"
ACCENT        = "#2563EB"
ACCENT_HOVER  = "#1D4ED8"
SUCCESS       = "#059669"
DANGER        = "#DC2626"
WARNING       = "#D97706"
TEXT_PRIMARY  = "#F1F5F9"
TEXT_SECONDARY= "#94A3B8"
TEXT_MUTED    = "#475569"
BORDER        = "#1E293B"
HIGHLIGHT     = "#3B82F6"

def _hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def _blend(c1, c2, t):
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"

def run_in_thread(fn, callback=None, error_callback=None):
    def wrapper():
        try:
            result = fn()
            if callback:
                callback(result)
        except Exception as exc:
            if error_callback:
                error_callback(exc)
    t = threading.Thread(target=wrapper, daemon=True)
    t.start()

class StyledButton(tk.Frame):
    def __init__(self, parent, text, command, color=ACCENT, hover_color=ACCENT_HOVER,
                 width=200, height=42, text_color=TEXT_PRIMARY, **kwargs):
        try:
            bg = parent.cget("bg")
        except Exception:
            bg = PRIMARY
        super().__init__(parent, bg=bg, **kwargs)
        self._color = color
        self._hover = hover_color
        self._cmd   = command

        self._btn = tk.Label(
            self, text=text,
            bg=color, fg=text_color,
            font=("Segoe UI", 10, "bold"),
            width=max(1, width // 8),
            height=2,
            cursor="hand2",
            relief="flat",
            padx=12, pady=4,
        )
        self._btn.pack(fill="both", expand=True)

        self._btn.bind("<Enter>",          lambda e: self._btn.config(bg=hover_color))
        self._btn.bind("<Leave>",          lambda e: self._btn.config(bg=color))
        self._btn.bind("<Button-1>",       lambda e: self._btn.config(bg=_blend(color, "#000000", 0.25)))
        self._btn.bind("<ButtonRelease-1>", lambda e: (self._btn.config(bg=hover_color), command()))

class EntryField(tk.Frame):
    def __init__(self, parent, label, show=None, **kwargs):
        super().__init__(parent, bg=PANEL, **kwargs)
        tk.Label(self, text=label, bg=PANEL, fg=TEXT_SECONDARY,
                 font=("Segoe UI", 9)).pack(anchor="w", padx=2, pady=(0, 4))
        container = tk.Frame(self, bg=BORDER, padx=1, pady=1)
        container.pack(fill="x")
        inner = tk.Frame(container, bg=CARD)
        inner.pack(fill="x")
        self.entry = tk.Entry(inner, show=show, bg=CARD, fg=TEXT_PRIMARY,
                              insertbackground=HIGHLIGHT,
                              relief="flat", font=("Segoe UI", 10),
                              bd=8)
        self.entry.pack(fill="x")
        self.entry.bind("<FocusIn>",  lambda e: container.config(bg=HIGHLIGHT))
        self.entry.bind("<FocusOut>", lambda e: container.config(bg=BORDER))

    def get(self):
        return self.entry.get().strip()

    def delete(self):
        self.entry.delete(0, tk.END)

    def set(self, value):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, str(value))

class ScrollableFrame(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        canvas = tk.Canvas(self, bg=kwargs.get("bg", PANEL),
                           highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.inner = tk.Frame(canvas, bg=kwargs.get("bg", PANEL))
        self.inner.bind("<Configure>",
                        lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("School Management System")
        self.geometry("1100x720")
        self.minsize(900, 600)
        self.configure(bg=PRIMARY)
        self.resizable(True, True)

        self.current_user  = None
        self.user_role     = None
        self._loading_count = 0
        self._loading_lbl   = None

        try:
            create_tables()
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))

        self._build_style()
        self._show_login()

    def _build_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview",
                        background=CARD,
                        foreground=TEXT_PRIMARY,
                        rowheight=32,
                        fieldbackground=CARD,
                        borderwidth=0,
                        font=("Segoe UI", 9))
        style.configure("Treeview.Heading",
                        background=SECONDARY,
                        foreground=TEXT_SECONDARY,
                        borderwidth=0,
                        font=("Segoe UI", 9, "bold"))
        style.map("Treeview",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", TEXT_PRIMARY)])
        style.configure("TScrollbar",
                        background=CARD,
                        troughcolor=SECONDARY,
                        borderwidth=0,
                        arrowcolor=TEXT_MUTED)

    def _show_loading(self):
        self._loading_count += 1
        if self._loading_lbl is None or not self._loading_lbl.winfo_exists():
            self._loading_lbl = tk.Label(
                self,
                text="⏳  Processing, please wait...",
                bg=ACCENT, fg=TEXT_PRIMARY,
                font=("Segoe UI", 10, "bold"),
                padx=20, pady=10,
                relief="flat",
            )
        self._loading_lbl.place(relx=0.5, rely=1.0, anchor="s", y=-2)
        self._loading_lbl.lift()

    def _hide_loading(self):
        self._loading_count = max(0, self._loading_count - 1)
        if self._loading_count == 0:
            if self._loading_lbl is not None and self._loading_lbl.winfo_exists():
                self._loading_lbl.place_forget()

    def _run(self, fn, callback=None, error_callback=None):
        self._show_loading()

        def wrapped_callback(result):
            self.after(0, self._hide_loading)
            if callback:
                callback(result)

        def wrapped_error(exc):
            self.after(0, self._hide_loading)
            if error_callback:
                error_callback(exc)

        run_in_thread(fn, wrapped_callback, wrapped_error)

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()
        self._loading_lbl = None

    def _show_login(self):
        self._clear()
        self.geometry("520x640")
        self.configure(bg=PRIMARY)

        outer = tk.Frame(self, bg=PRIMARY)
        outer.place(relx=0.5, rely=0.5, anchor="center")

        logo_f = tk.Frame(outer, bg=PRIMARY)
        logo_f.pack(pady=(0, 24))
        tk.Label(logo_f, text="▣", bg=PRIMARY, fg=ACCENT,
                 font=("Segoe UI", 36)).pack()
        tk.Label(logo_f, text="School Management System",
                 bg=PRIMARY, fg=TEXT_PRIMARY,
                 font=("Segoe UI", 16, "bold")).pack()
        tk.Label(logo_f, text="Sign in to your account",
                 bg=PRIMARY, fg=TEXT_SECONDARY,
                 font=("Segoe UI", 10)).pack(pady=(4, 0))

        card = tk.Frame(outer, bg=PANEL, padx=40, pady=36)
        card.pack(fill="x", ipadx=20)

        self._role_var = tk.StringVar(value="student")
        role_f = tk.Frame(card, bg=BORDER, padx=1, pady=1)
        role_f.pack(fill="x", pady=(0, 20))
        inner_r = tk.Frame(role_f, bg=CARD)
        inner_r.pack(fill="x")
        for col, (label, val) in enumerate([("Student", "student"), ("Teacher", "teacher")]):
            btn = tk.Radiobutton(inner_r, text=label, variable=self._role_var,
                                 value=val, bg=CARD, fg=TEXT_SECONDARY,
                                 activebackground=ACCENT, activeforeground=TEXT_PRIMARY,
                                 selectcolor=ACCENT, indicatoron=False,
                                 font=("Segoe UI", 10), padx=20, pady=8,
                                 relief="flat", bd=0,
                                 command=self._toggle_login_fields)
            btn.grid(row=0, column=col, sticky="nsew")
            inner_r.columnconfigure(col, weight=1)

        self._login_fields_frame = tk.Frame(card, bg=PANEL)
        self._login_fields_frame.pack(fill="x")
        self._build_login_fields()

        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", pady=20)
        tk.Label(card, text="Don't have an account?",
                 bg=PANEL, fg=TEXT_MUTED,
                 font=("Segoe UI", 9)).pack()
        StyledButton(card, "Create Account", self._show_register,
                     color=CARD, hover_color=BORDER,
                     text_color=TEXT_SECONDARY, width=320, height=38).pack(pady=(8, 0))

    def _build_login_fields(self):
        for w in self._login_fields_frame.winfo_children():
            w.destroy()

        role = self._role_var.get()

        self._ln_firstname = EntryField(self._login_fields_frame, "First Name")
        self._ln_firstname.pack(fill="x", pady=(0, 14))
        self._ln_lastname = EntryField(self._login_fields_frame, "Last Name")
        self._ln_lastname.pack(fill="x", pady=(0, 14))

        if role == "teacher":
            self._ln_branch = EntryField(self._login_fields_frame, "Branch")
            self._ln_branch.pack(fill="x", pady=(0, 14))
        else:
            self._ln_branch = None

        self._ln_password = EntryField(self._login_fields_frame, "Password", show="●")
        self._ln_password.pack(fill="x", pady=(0, 20))
        StyledButton(self._login_fields_frame, "Sign In", self._do_login,
                     width=320, height=42).pack()

    def _toggle_login_fields(self):
        self._build_login_fields()

    def _do_login(self):
        fn  = self._ln_firstname.get()
        ln  = self._ln_lastname.get()
        pwd = self._ln_password.get()
        role = self._role_var.get()

        if not fn or not ln or not pwd:
            messagebox.showwarning("Missing Fields", "Please fill in all required fields.")
            return

        if role == "teacher":
            branch = self._ln_branch.get() if self._ln_branch else ""
            if not branch:
                messagebox.showwarning("Missing Fields", "Branch is required for teachers.")
                return
            def do():
                return loginasteacher(fn, ln, branch, pwd)
            def on_success(result):
                if result:
                    self.current_user = result
                    self.user_role = "teacher"
                    self.after(0, self._show_teacher_panel)
                else:
                    self.after(0, lambda: messagebox.showerror("Login Failed", "Invalid credentials. Please try again."))
            def on_error(exc):
                self.after(0, lambda: messagebox.showerror("Error", str(exc)))
            self._run(do, on_success, on_error)
        else:
            def do():
                return loginasstudent(fn, ln, pwd)
            def on_success(result):
                if result:
                    self.current_user = result
                    self.user_role = "student"
                    self.after(0, self._show_student_panel)
                else:
                    self.after(0, lambda: messagebox.showerror("Login Failed", "Invalid credentials. Please try again."))
            def on_error(exc):
                self.after(0, lambda: messagebox.showerror("Error", str(exc)))
            self._run(do, on_success, on_error)

    def _show_register(self):
        self._clear()
        self.geometry("560x680")
        self.configure(bg=PRIMARY)

        outer = tk.Frame(self, bg=PRIMARY)
        outer.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(outer, text="▣", bg=PRIMARY, fg=ACCENT,
                 font=("Segoe UI", 28)).pack()
        tk.Label(outer, text="Create Account",
                 bg=PRIMARY, fg=TEXT_PRIMARY,
                 font=("Segoe UI", 16, "bold")).pack()
        tk.Label(outer, text="Join the School Management System",
                 bg=PRIMARY, fg=TEXT_SECONDARY,
                 font=("Segoe UI", 10)).pack(pady=(4, 16))

        card = tk.Frame(outer, bg=PANEL, padx=40, pady=32)
        card.pack(fill="x")

        self._reg_role_var = tk.StringVar(value="student")
        role_f = tk.Frame(card, bg=BORDER, padx=1, pady=1)
        role_f.pack(fill="x", pady=(0, 20))
        inner_r = tk.Frame(role_f, bg=CARD)
        inner_r.pack(fill="x")
        for col, (label, val) in enumerate([("Student", "student"), ("Teacher", "teacher")]):
            btn = tk.Radiobutton(inner_r, text=label, variable=self._reg_role_var,
                                 value=val, bg=CARD, fg=TEXT_SECONDARY,
                                 activebackground=ACCENT, activeforeground=TEXT_PRIMARY,
                                 selectcolor=ACCENT, indicatoron=False,
                                 font=("Segoe UI", 10), padx=20, pady=8,
                                 relief="flat", bd=0,
                                 command=self._rebuild_reg_fields)
            btn.grid(row=0, column=col, sticky="nsew")
            inner_r.columnconfigure(col, weight=1)

        self._reg_fields_frame = tk.Frame(card, bg=PANEL)
        self._reg_fields_frame.pack(fill="x")
        self._build_reg_fields()

        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", pady=16)
        back_f = tk.Frame(card, bg=PANEL)
        back_f.pack()
        tk.Label(back_f, text="Already have an account?",
                 bg=PANEL, fg=TEXT_MUTED,
                 font=("Segoe UI", 9)).pack(side="left", padx=(0, 8))
        StyledButton(back_f, "Sign In", self._show_login,
                     color=CARD, hover_color=BORDER,
                     text_color=TEXT_SECONDARY, width=100, height=32).pack(side="left")

    def _build_reg_fields(self):
        for w in self._reg_fields_frame.winfo_children():
            w.destroy()

        role = self._reg_role_var.get()

        row1 = tk.Frame(self._reg_fields_frame, bg=PANEL)
        row1.pack(fill="x", pady=(0, 14))
        fn_f = EntryField(row1, "First Name")
        fn_f.pack(side="left", expand=True, fill="x", padx=(0, 8))
        ln_f = EntryField(row1, "Last Name")
        ln_f.pack(side="left", expand=True, fill="x")
        self._reg_fn = fn_f
        self._reg_ln = ln_f

        if role == "student":
            self._reg_class = EntryField(self._reg_fields_frame, "Class (e.g. 10-A)")
            self._reg_class.pack(fill="x", pady=(0, 14))
            self._reg_branch = None
        else:
            self._reg_branch = EntryField(self._reg_fields_frame, "Branch / Subject")
            self._reg_branch.pack(fill="x", pady=(0, 14))
            self._reg_class = None

        self._reg_pwd = EntryField(self._reg_fields_frame, "Password", show="●")
        self._reg_pwd.pack(fill="x", pady=(0, 14))
        self._reg_pwd2 = EntryField(self._reg_fields_frame, "Confirm Password", show="●")
        self._reg_pwd2.pack(fill="x", pady=(0, 20))
        StyledButton(self._reg_fields_frame, "Create Account", self._do_register,
                     width=380, height=42).pack()

    def _rebuild_reg_fields(self):
        self._build_reg_fields()

    def _do_register(self):
        fn  = self._reg_fn.get()
        ln  = self._reg_ln.get()
        pwd = self._reg_pwd.get()
        pwd2 = self._reg_pwd2.get()
        role = self._reg_role_var.get()

        if not fn or not ln or not pwd:
            messagebox.showwarning("Missing Fields", "Please fill in all fields.")
            return
        if pwd != pwd2:
            messagebox.showerror("Password Mismatch", "Passwords do not match.")
            return

        if role == "student":
            classname = self._reg_class.get()
            if not classname:
                messagebox.showwarning("Missing Fields", "Class is required.")
                return
            def do():
                snum = generate_student_number()
                signupasstudent(fn, ln, snum, classname, pwd)
                return snum
            def on_success(snum):
                self.after(0, lambda: (
                    messagebox.showinfo("Account Created",
                                        f"Student account created!\nYour Student Number: {snum}\nPlease save this number."),
                    self._show_login()
                ))
            def on_error(exc):
                self.after(0, lambda: messagebox.showerror("Error", str(exc)))
            self._run(do, on_success, on_error)
        else:
            branch = self._reg_branch.get()
            if not branch:
                messagebox.showwarning("Missing Fields", "Branch is required.")
                return
            def do():
                signupasteacher(fn, ln, branch, pwd)
            def on_success(_):
                self.after(0, lambda: (
                    messagebox.showinfo("Account Created", "Teacher account created successfully!"),
                    self._show_login()
                ))
            def on_error(exc):
                self.after(0, lambda: messagebox.showerror("Error", str(exc)))
            self._run(do, on_success, on_error)

    def _topbar(self, parent, title, subtitle=""):
        bar = tk.Frame(parent, bg=SECONDARY, padx=24, pady=16)
        bar.pack(fill="x")
        left = tk.Frame(bar, bg=SECONDARY)
        left.pack(side="left")
        tk.Label(left, text="▣", bg=SECONDARY, fg=ACCENT,
                 font=("Segoe UI", 18)).pack(side="left", padx=(0, 10))
        text_f = tk.Frame(left, bg=SECONDARY)
        text_f.pack(side="left")
        tk.Label(text_f, text=title, bg=SECONDARY, fg=TEXT_PRIMARY,
                 font=("Segoe UI", 13, "bold")).pack(anchor="w")
        if subtitle:
            tk.Label(text_f, text=subtitle, bg=SECONDARY, fg=TEXT_MUTED,
                     font=("Segoe UI", 9)).pack(anchor="w")
        right = tk.Frame(bar, bg=SECONDARY)
        right.pack(side="right")
        StyledButton(right, "Sign Out", self._sign_out,
                     color=CARD, hover_color=DANGER,
                     text_color=TEXT_SECONDARY, width=100, height=34).pack()
        return bar

    def _sign_out(self):
        self.current_user = None
        self.user_role = None
        self._show_login()

    def _show_teacher_panel(self):
        self._clear()
        self.geometry("1100x720")
        self.configure(bg=PRIMARY)

        data  = self.current_user
        fname = data[1]
        lname = data[2]
        branch = data[3]

        self._topbar(self, "School Management System",
                     f"Teacher  ·  {fname} {lname}  ·  {branch}")

        body = tk.Frame(self, bg=PRIMARY)
        body.pack(fill="both", expand=True)

        sidebar = tk.Frame(body, bg=SECONDARY, width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="NAVIGATION", bg=SECONDARY, fg=TEXT_MUTED,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=20, pady=(24, 8))

        self._teacher_content = tk.Frame(body, bg=PRIMARY)
        self._teacher_content.pack(side="left", fill="both", expand=True)

        nav_items = [
            ("📋  Class Roster",    self._teacher_roster),
            ("✏️   Update Grade",    self._teacher_update_grade),
            ("➕  Add Grade",       self._teacher_add_grade),
            ("📊  Student Report",  self._teacher_report),
            ("🗑️   Remove Student",  self._teacher_remove_student),
        ]
        for label, cmd in nav_items:
            self._nav_btn(sidebar, label, cmd)

        self._teacher_roster()

    def _nav_btn(self, parent, label, cmd):
        f = tk.Frame(parent, bg=SECONDARY, cursor="hand2")
        f.pack(fill="x", pady=1)
        lbl = tk.Label(f, text=label, bg=SECONDARY, fg=TEXT_SECONDARY,
                       font=("Segoe UI", 10), padx=20, pady=10, anchor="w")
        lbl.pack(fill="x")
        for w in (f, lbl):
            w.bind("<Enter>", lambda e, fr=f, lb=lbl: (fr.config(bg=CARD), lb.config(bg=CARD, fg=TEXT_PRIMARY)))
            w.bind("<Leave>", lambda e, fr=f, lb=lbl: (fr.config(bg=SECONDARY), lb.config(bg=SECONDARY, fg=TEXT_SECONDARY)))
            w.bind("<Button-1>", lambda e, c=cmd: c())

    def _clear_content(self, frame):
        for w in frame.winfo_children():
            w.destroy()

    def _section_header(self, parent, title, subtitle=""):
        hdr = tk.Frame(parent, bg=PRIMARY, padx=32, pady=24)
        hdr.pack(fill="x")
        tk.Label(hdr, text=title, bg=PRIMARY, fg=TEXT_PRIMARY,
                 font=("Segoe UI", 16, "bold")).pack(anchor="w")
        if subtitle:
            tk.Label(hdr, text=subtitle, bg=PRIMARY, fg=TEXT_MUTED,
                     font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 0))
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=32)

    def _teacher_roster(self):
        self._clear_content(self._teacher_content)
        self._section_header(self._teacher_content, "Class Roster",
                             "View students by class")
        body = tk.Frame(self._teacher_content, bg=PRIMARY, padx=32, pady=20)
        body.pack(fill="both", expand=True)

        top = tk.Frame(body, bg=PRIMARY)
        top.pack(fill="x", pady=(0, 16))
        tk.Label(top, text="Class Name:", bg=PRIMARY, fg=TEXT_SECONDARY,
                 font=("Segoe UI", 10)).pack(side="left", padx=(0, 8))
        class_var = tk.StringVar()
        entry = tk.Entry(top, textvariable=class_var, bg=CARD, fg=TEXT_PRIMARY,
                         insertbackground=HIGHLIGHT, relief="flat",
                         font=("Segoe UI", 10), bd=8, width=16)
        entry.pack(side="left", padx=(0, 10))

        tree_f = tk.Frame(body, bg=CARD)
        tree_f.pack(fill="both", expand=True)

        cols = ("Name", "Student Number")
        tree = ttk.Treeview(tree_f, columns=cols, show="headings", height=18)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=220, anchor="center")
        tree.pack(fill="both", expand=True, padx=2, pady=2)

        def search():
            def do():
                return getstudentsbyclass(class_var.get())
            def on_success(students):
                def update():
                    for row in tree.get_children():
                        tree.delete(row)
                    for s in students:
                        tree.insert("", "end", values=(f"{s[0]} {s[1]}", s[2]))
                self.after(0, update)
            def on_error(exc):
                self.after(0, lambda: messagebox.showerror("Error", str(exc)))
            self._run(do, on_success, on_error)

        StyledButton(top, "Search", search, width=100, height=36).pack(side="left")

    def _teacher_update_grade(self):
        self._clear_content(self._teacher_content)
        self._section_header(self._teacher_content, "Update Grade",
                             "Modify an existing grade entry")
        body = tk.Frame(self._teacher_content, bg=PRIMARY, padx=32, pady=20)
        body.pack(fill="x")

        snum_f  = EntryField(body, "Student Number")
        snum_f.pack(fill="x", pady=(0, 14))
        lesson_f = EntryField(body, "Lesson Name")
        lesson_f.pack(fill="x", pady=(0, 14))

        current_frame = tk.Frame(body, bg=CARD, padx=16, pady=12)
        current_frame.pack(fill="x", pady=(0, 14))
        tk.Label(current_frame, text="Current Grades", bg=CARD, fg=TEXT_MUTED,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w")
        grades_row = tk.Frame(current_frame, bg=CARD)
        grades_row.pack(fill="x", pady=(6, 0))
        self._cur_g1_lbl   = tk.Label(grades_row, text="Exam 1: —", bg=CARD, fg=TEXT_SECONDARY, font=("Segoe UI", 9))
        self._cur_g1_lbl.pack(side="left", padx=(0, 20))
        self._cur_g2_lbl   = tk.Label(grades_row, text="Exam 2: —", bg=CARD, fg=TEXT_SECONDARY, font=("Segoe UI", 9))
        self._cur_g2_lbl.pack(side="left", padx=(0, 20))
        self._cur_perf_lbl = tk.Label(grades_row, text="Performance: —", bg=CARD, fg=TEXT_SECONDARY, font=("Segoe UI", 9))
        self._cur_perf_lbl.pack(side="left")

        def load_current_grades():
            raw_snum = snum_f.get()
            raw_lesson = lesson_f.get()
            if not raw_snum or not raw_lesson:
                return
            try:
                snum = int(raw_snum)
            except ValueError:
                return
            def do():
                return getmygrades(snum)
            def on_success(grades):
                def update():
                    g1_val = perf_val = g2_val = None
                    if isinstance(grades, list):
                        for row in grades:
                            if row[0].strip().lower() == raw_lesson.strip().lower():
                                g1_val   = row[1]
                                g2_val   = row[2]
                                perf_val = row[3]
                                break
                    self._cur_g1_lbl.config(text=f"Exam 1: {g1_val if g1_val is not None else '—'}")
                    self._cur_g2_lbl.config(text=f"Exam 2: {g2_val if g2_val is not None else '—'}")
                    self._cur_perf_lbl.config(text=f"Performance: {perf_val if perf_val is not None else '—'}")
                self.after(0, update)
            self._run(do, on_success)

        load_btn = StyledButton(body, "Load Current Grades", load_current_grades,
                                color=CARD, hover_color=BORDER,
                                text_color=TEXT_SECONDARY, width=200, height=36)
        load_btn.pack(anchor="w", pady=(0, 14))

        tk.Label(body, text="Leave fields blank to keep existing value", bg=PRIMARY, fg=TEXT_MUTED,
                 font=("Segoe UI", 8)).pack(anchor="w", pady=(0, 8))

        new_row = tk.Frame(body, bg=PRIMARY)
        new_row.pack(fill="x", pady=(0, 14))
        g1_f   = EntryField(new_row, "New Exam 1 (blank = no change)")
        g1_f.pack(side="left", expand=True, fill="x", padx=(0, 8))
        g2_f   = EntryField(new_row, "New Exam 2 (blank = no change)")
        g2_f.pack(side="left", expand=True, fill="x", padx=(0, 8))
        perf_f = EntryField(new_row, "New Performance (blank = no change)")
        perf_f.pack(side="left", expand=True, fill="x")

        def _validate_score(value, field_name):
            if value == "":
                return None
            try:
                v = int(value)
            except ValueError:
                raise ValueError(f"{field_name} must be a whole number.")
            if v < 0 or v > 100:
                raise ValueError(f"{field_name} must be between 0 and 100.")
            return v

        def submit():
            try:
                snum   = int(snum_f.get())
                lesson = lesson_f.get()
                if not lesson:
                    raise ValueError("Lesson name is required.")
                new_g1   = _validate_score(g1_f.get(),   "Exam 1")
                new_g2   = _validate_score(g2_f.get(),   "Exam 2")
                new_perf = _validate_score(perf_f.get(), "Performance")
                if new_g1 is None and new_g2 is None and new_perf is None:
                    messagebox.showwarning("Nothing to Update", "Enter at least one new score.")
                    return
            except ValueError as ve:
                messagebox.showerror("Invalid Input", str(ve))
                return

            def do():
                if new_g1 is not None:
                    updategrade(snum, lesson, "grade1", new_g1)
                if new_g2 is not None:
                    updategrade(snum, lesson, "grade2", new_g2)
                if new_perf is not None:
                    updategrade(snum, lesson, "performance", new_perf)
            def on_success(_):
                self.after(0, lambda: messagebox.showinfo("Success", "Grade(s) updated successfully."))
            def on_error(exc):
                self.after(0, lambda: messagebox.showerror("Error", str(exc)))
            self._run(do, on_success, on_error)

        StyledButton(body, "Update Grade", submit, width=240, height=42).pack(pady=(4, 0))

    def _teacher_add_grade(self):
        self._clear_content(self._teacher_content)
        self._section_header(self._teacher_content, "Add Grade",
                             "Add or update a grade record for a student")
        body = tk.Frame(self._teacher_content, bg=PRIMARY, padx=32, pady=20)
        body.pack(fill="x")

        tk.Label(body, text="Leave exam fields blank to skip updating them", bg=PRIMARY, fg=TEXT_MUTED,
                 font=("Segoe UI", 8)).pack(anchor="w", pady=(0, 10))

        snum_f  = EntryField(body, "Student Number")
        snum_f.pack(fill="x", pady=(0, 14))
        lesson_f = EntryField(body, "Lesson Name")
        lesson_f.pack(fill="x", pady=(0, 14))

        grade_row = tk.Frame(body, bg=PRIMARY)
        grade_row.pack(fill="x", pady=(0, 14))
        g1_f   = EntryField(grade_row, "Exam 1 (blank = skip)")
        g1_f.pack(side="left", expand=True, fill="x", padx=(0, 8))
        g2_f   = EntryField(grade_row, "Exam 2 (blank = skip)")
        g2_f.pack(side="left", expand=True, fill="x", padx=(0, 8))
        perf_f = EntryField(grade_row, "Performance (blank = skip)")
        perf_f.pack(side="left", expand=True, fill="x")

        def _validate_score(value, field_name):
            if value == "":
                return None
            try:
                v = int(value)
            except ValueError:
                raise ValueError(f"{field_name} must be a whole number.")
            if v < 0 or v > 100:
                raise ValueError(f"{field_name} must be between 0 and 100.")
            return v

        def submit():
            try:
                raw_snum = snum_f.get()
                if not raw_snum:
                    raise ValueError("Student Number is required.")
                snum = int(raw_snum)
                lesson = lesson_f.get()
                if not lesson:
                    raise ValueError("Lesson name is required.")
                g1   = _validate_score(g1_f.get(),   "Exam 1")
                g2   = _validate_score(g2_f.get(),   "Exam 2")
                perf = _validate_score(perf_f.get(), "Performance")
                if g1 is None and g2 is None and perf is None:
                    messagebox.showwarning("Nothing to Save", "Enter at least one exam score.")
                    return
            except ValueError as ve:
                messagebox.showerror("Invalid Input", str(ve))
                return

            def do():
                existing = getmygrades(snum)
                record_exists = False
                if isinstance(existing, list):
                    for row in existing:
                        if row[0].strip().lower() == lesson.strip().lower():
                            record_exists = True
                            break

                if record_exists:
                    if g1 is not None:
                        updategrade(snum, lesson, "grade1", g1)
                    if g2 is not None:
                        updategrade(snum, lesson, "grade2", g2)
                    if perf is not None:
                        updategrade(snum, lesson, "performance", perf)
                else:
                    safe_g1   = g1   if g1   is not None else 0
                    safe_g2   = g2   if g2   is not None else 0
                    safe_perf = perf if perf is not None else 0
                    addgrade(snum, lesson, safe_g1, safe_g2, safe_perf)
                    if g1 is None:
                        updategrade(snum, lesson, "grade1", None)
                    if g2 is None:
                        updategrade(snum, lesson, "grade2", None)
                    if perf is None:
                        updategrade(snum, lesson, "performance", None)

            def on_success(_):
                self.after(0, lambda: messagebox.showinfo("Success", "Grade saved successfully."))
            def on_error(exc):
                self.after(0, lambda: messagebox.showerror("Error", str(exc)))
            self._run(do, on_success, on_error)

        StyledButton(body, "Save Grade", submit, width=240, height=42).pack(pady=(4, 0))

    def _teacher_report(self):
        self._clear_content(self._teacher_content)
        self._section_header(self._teacher_content, "Student Report",
                             "View full grade report for a student")
        body = tk.Frame(self._teacher_content, bg=PRIMARY, padx=32, pady=20)
        body.pack(fill="both", expand=True)

        top = tk.Frame(body, bg=PRIMARY)
        top.pack(fill="x", pady=(0, 16))
        tk.Label(top, text="Student Number:", bg=PRIMARY, fg=TEXT_SECONDARY,
                 font=("Segoe UI", 10)).pack(side="left", padx=(0, 8))
        snum_var = tk.StringVar()
        entry = tk.Entry(top, textvariable=snum_var, bg=CARD, fg=TEXT_PRIMARY,
                         insertbackground=HIGHLIGHT, relief="flat",
                         font=("Segoe UI", 10), bd=8, width=16)
        entry.pack(side="left", padx=(0, 10))

        tree_f = tk.Frame(body, bg=CARD)
        tree_f.pack(fill="both", expand=True, pady=(10, 0))

        cols = ("Lesson", "Average", "Status")
        tree = ttk.Treeview(tree_f, columns=cols, show="headings", height=16)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=180, anchor="center")
        tree.pack(fill="both", expand=True, padx=2, pady=2)
        tree.tag_configure("passed", foreground=SUCCESS)
        tree.tag_configure("failed", foreground=DANGER)

        def search():
            try:
                snum = int(snum_var.get())
            except ValueError:
                messagebox.showerror("Invalid", "Enter a valid student number.")
                return
            def do():
                return getstudentreports(snum)
            def on_success(report):
                def update():
                    for row in tree.get_children():
                        tree.delete(row)
                    for item in report:
                        status = item["Status:"]
                        tag = "passed" if status == "Passed" else "failed"
                        tree.insert("", "end",
                                    values=(item["Lesson:"], item["Average:"], status),
                                    tags=(tag,))
                self.after(0, update)
            def on_error(exc):
                self.after(0, lambda: messagebox.showerror("Error", str(exc)))
            self._run(do, on_success, on_error)

        StyledButton(top, "Get Report", search, width=130, height=36).pack(side="left")

    def _teacher_remove_student(self):
        self._clear_content(self._teacher_content)
        self._section_header(self._teacher_content, "Remove Student",
                             "Permanently delete a student and their records")
        body = tk.Frame(self._teacher_content, bg=PRIMARY, padx=32, pady=24)
        body.pack(fill="x")

        warn = tk.Frame(body, bg="#3B1F1F", padx=16, pady=12)
        warn.pack(fill="x", pady=(0, 24))
        tk.Label(warn, text="⚠  This action is irreversible. All grade records will also be deleted.",
                 bg="#3B1F1F", fg=WARNING, font=("Segoe UI", 10)).pack(anchor="w")

        f = EntryField(body, "Student Number")
        f.pack(fill="x", pady=(0, 20))

        def submit():
            try:
                snum = int(f.get())
            except ValueError:
                messagebox.showerror("Invalid", "Enter a valid student number.")
                return
            if messagebox.askyesno("Confirm Deletion",
                                   f"Permanently delete student #{snum} and all their records?"):
                def do():
                    deletestudent(snum)
                def on_success(_):
                    def update():
                        messagebox.showinfo("Deleted", f"Student #{snum} has been removed.")
                        f.delete()
                    self.after(0, update)
                def on_error(exc):
                    self.after(0, lambda: messagebox.showerror("Error", str(exc)))
                self._run(do, on_success, on_error)

        StyledButton(body, "Remove Student", submit,
                     color=DANGER, hover_color="#991B1B",
                     width=200, height=42).pack()

    def _show_student_panel(self):
        self._clear()
        self.geometry("1000x680")
        self.configure(bg=PRIMARY)

        data = self.current_user
        fname  = data[1]
        lname  = data[2]
        snum   = data[3]
        cls    = data[4]

        self._topbar(self, "School Management System",
                     f"Student  ·  {fname} {lname}  ·  #{snum}  ·  Class {cls}")

        body = tk.Frame(self, bg=PRIMARY)
        body.pack(fill="both", expand=True)

        sidebar = tk.Frame(body, bg=SECONDARY, width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="NAVIGATION", bg=SECONDARY, fg=TEXT_MUTED,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=20, pady=(24, 8))

        self._student_content = tk.Frame(body, bg=PRIMARY)
        self._student_content.pack(side="left", fill="both", expand=True)

        nav_items = [
            ("👤  My Profile",      self._student_profile),
            ("📊  My Grades",       self._student_grades),
            ("👥  Classmates",      self._student_classmates),
            ("🔑  Change Password", self._student_change_password),
        ]
        for label, cmd in nav_items:
            self._nav_btn(sidebar, label, cmd)

        self._student_profile()

    def _student_profile(self):
        self._clear_content(self._student_content)
        self._section_header(self._student_content, "My Profile")
        body = tk.Frame(self._student_content, bg=PRIMARY, padx=32, pady=28)
        body.pack(fill="x")

        data = self.current_user
        snum = data[3]

        avatar = tk.Frame(body, bg=ACCENT, width=72, height=72)
        avatar.pack(pady=(0, 20))
        avatar.pack_propagate(False)
        initials = f"{data[1][0]}{data[2][0]}" if data[1] and data[2] else "?"
        tk.Label(avatar, text=initials.upper(), bg=ACCENT, fg=TEXT_PRIMARY,
                 font=("Segoe UI", 22, "bold")).place(relx=0.5, rely=0.5, anchor="center")

        rows_frame = tk.Frame(body, bg=PRIMARY)
        rows_frame.pack(fill="x")

        def load_profile():
            def do():
                return getstudentprofile(snum)
            def on_success(profile):
                def update():
                    rows = [
                        ("First Name",      profile[0] if profile else data[1]),
                        ("Last Name",       profile[1] if profile else data[2]),
                        ("Student Number",  snum),
                        ("Class",           profile[2] if profile else data[4]),
                    ]
                    for w in rows_frame.winfo_children():
                        w.destroy()
                    for label, value in rows:
                        row = tk.Frame(rows_frame, bg=CARD, padx=20, pady=14)
                        row.pack(fill="x", pady=(0, 8))
                        tk.Label(row, text=label, bg=CARD, fg=TEXT_MUTED,
                                 font=("Segoe UI", 9), width=18, anchor="w").pack(side="left")
                        tk.Label(row, text=str(value), bg=CARD, fg=TEXT_PRIMARY,
                                 font=("Segoe UI", 10, "bold"), anchor="w").pack(side="left")
                self.after(0, update)
            def on_error(_):
                def fallback():
                    rows = [
                        ("First Name",     data[1]),
                        ("Last Name",      data[2]),
                        ("Student Number", snum),
                        ("Class",          data[4]),
                    ]
                    for label, value in rows:
                        row = tk.Frame(rows_frame, bg=CARD, padx=20, pady=14)
                        row.pack(fill="x", pady=(0, 8))
                        tk.Label(row, text=label, bg=CARD, fg=TEXT_MUTED,
                                 font=("Segoe UI", 9), width=18, anchor="w").pack(side="left")
                        tk.Label(row, text=str(value), bg=CARD, fg=TEXT_PRIMARY,
                                 font=("Segoe UI", 10, "bold"), anchor="w").pack(side="left")
                self.after(0, fallback)
            self._run(do, on_success, on_error)

        load_profile()

    def _student_grades(self):
        self._clear_content(self._student_content)
        self._section_header(self._student_content, "My Grades",
                             "Your academic performance")
        body = tk.Frame(self._student_content, bg=PRIMARY, padx=32, pady=20)
        body.pack(fill="both", expand=True)

        snum = self.current_user[3]

        tree_f = tk.Frame(body, bg=CARD)
        tree_f.pack(fill="both", expand=True)

        cols = ("Lesson", "Exam 1", "Exam 2", "Performance", "Average", "Status")
        tree = ttk.Treeview(tree_f, columns=cols, show="headings", height=18)
        col_widths = [180, 80, 80, 100, 90, 90]
        for col, w in zip(cols, col_widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")
        tree.pack(fill="both", expand=True, padx=2, pady=2)
        tree.tag_configure("passed", foreground=SUCCESS)
        tree.tag_configure("failed", foreground=DANGER)

        def do():
            return getmygrades(snum)
        def on_success(grades):
            def update():
                if isinstance(grades, str):
                    tk.Label(body, text=grades, bg=PRIMARY, fg=TEXT_MUTED,
                             font=("Segoe UI", 12)).pack(pady=40)
                    return
                for g in grades:
                    lesson, g1, g2, perf = g
                    vals = [v for v in [g1, g2, perf] if v is not None]
                    avg = round(sum(vals) / len(vals), 2) if vals else 0
                    status = "Passed" if avg >= 50 else "Failed"
                    tag = "passed" if status == "Passed" else "failed"
                    tree.insert("", "end",
                                values=(lesson, g1 or "-", g2 or "-", perf or "-", avg, status),
                                tags=(tag,))
            self.after(0, update)
        def on_error(exc):
            self.after(0, lambda: messagebox.showerror("Error", str(exc)))
        self._run(do, on_success, on_error)

    def _student_classmates(self):
        self._clear_content(self._student_content)
        self._section_header(self._student_content, "Classmates",
                             "Everyone in your class")
        body = tk.Frame(self._student_content, bg=PRIMARY, padx=32, pady=20)
        body.pack(fill="both", expand=True)

        cls = self.current_user[4]

        tree_f = tk.Frame(body, bg=CARD)
        tree_f.pack(fill="both", expand=True)

        cols = ("#", "First Name", "Last Name")
        tree = ttk.Treeview(tree_f, columns=cols, show="headings", height=20)
        for col in cols:
            tree.heading(col, text=col)
        tree.column("#", width=60, anchor="center")
        tree.column("First Name", width=200, anchor="w")
        tree.column("Last Name",  width=200, anchor="w")
        tree.pack(fill="both", expand=True, padx=2, pady=2)

        def do():
            return getclassmates(cls)
        def on_success(classmates):
            def update():
                for i, cm in enumerate(classmates, start=1):
                    tree.insert("", "end", values=(i, cm[0], cm[1]))
            self.after(0, update)
        def on_error(exc):
            self.after(0, lambda: messagebox.showerror("Error", str(exc)))
        self._run(do, on_success, on_error)

    def _student_change_password(self):
        self._clear_content(self._student_content)
        self._section_header(self._student_content, "Change Password",
                             "Update your login credentials")
        body = tk.Frame(self._student_content, bg=PRIMARY, padx=32, pady=24)
        body.pack(fill="x")

        old_f  = EntryField(body, "Current Password", show="●")
        old_f.pack(fill="x", pady=(0, 14))
        new_f  = EntryField(body, "New Password", show="●")
        new_f.pack(fill="x", pady=(0, 14))
        new_f2 = EntryField(body, "Confirm New Password", show="●")
        new_f2.pack(fill="x", pady=(0, 24))

        def submit():
            old  = old_f.get()
            new  = new_f.get()
            new2 = new_f2.get()
            if not old or not new or not new2:
                messagebox.showwarning("Missing Fields", "Please fill all fields.")
                return
            if new != new2:
                messagebox.showerror("Mismatch", "New passwords do not match.")
                return
            snum = self.current_user[3]
            def do():
                return changepassword(snum, old, new)
            def on_success(result):
                def update():
                    if result:
                        messagebox.showinfo("Success", "Password changed successfully.")
                        old_f.delete()
                        new_f.delete()
                        new_f2.delete()
                    else:
                        messagebox.showerror("Error", "Current password is incorrect.")
                self.after(0, update)
            def on_error(exc):
                self.after(0, lambda: messagebox.showerror("Error", str(exc)))
            self._run(do, on_success, on_error)

        StyledButton(body, "Change Password", submit, width=240, height=42).pack()


def check_internet(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except (socket.error, OSError):
        return False

if __name__ == "__main__":
    if not check_internet():
        _root = tk.Tk()
        _root.withdraw()
        messagebox.showerror(
            "No Internet",
            "Internet connection not found.\n\n"
            "Please check your connection and try again.",
        )
        _root.destroy()
        sys.exit(1)

    app = App()
    app.mainloop()