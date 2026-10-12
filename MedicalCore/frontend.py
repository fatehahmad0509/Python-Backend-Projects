import socket
import threading
from datetime import datetime

import customtkinter as ctk
from tkinter import messagebox, ttk
import tkinter as tk

import database
from database import get_connection
from doctorauth import DoctorAuth
from staffauth import StaffAuth


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

database.create_hospital_tables()

C_BG = "#0f1117"
C_SURFACE = "#1a1d27"
C_CARD = "#21253a"
C_BORDER = "#2e3350"
C_ACCENT = "#4f8ef7"
C_ACCENT2 = "#7c5cbf"
C_SUCCESS = "#34d399"
C_DANGER = "#f87171"
C_TEXT = "#e2e8f0"
C_MUTED = "#64748b"
C_BADGE = "#0d2040"

FONT_TITLE = ("Segoe UI", 28, "bold")
FONT_SUB = ("Segoe UI", 13)
FONT_LABEL = ("Segoe UI", 12)
FONT_SMALL = ("Segoe UI", 10)
FONT_BADGE = ("Segoe UI", 9, "bold")
FONT_MONO = ("Consolas", 11)

FILTER_STATUS_VALUES = ["All", "Waiting", "In Progress", "Completed", "Cancelled"]
APPOINTMENT_STATUS_VALUES = ["Waiting", "In Progress", "Completed", "Cancelled"]

app = None


def check_internet(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False

def status_key(status: str) -> str:
    return (status or "").strip().lower().replace(" ", "_")


def status_label(status: str) -> str:
    return {
        "waiting": "Waiting",
        "in_progress": "In Progress",
        "completed": "Completed",
        "cancelled": "Cancelled",
    }.get(status_key(status), (status or "Unknown").replace("_", " ").title())


def status_color(status: str) -> str:
    return {
        "waiting": "#f59e0b",
        "in_progress": C_ACCENT,
        "completed": C_SUCCESS,
        "cancelled": C_DANGER,
    }.get(status_key(status), C_TEXT)


def make_separator(parent, color=C_BORDER):
    return ctk.CTkFrame(parent, height=1, fg_color=color)


def run_in_thread(fn, *args, callback=None):
    def target():
        result = fn(*args)
        if callback and app is not None:
            app.after(0, lambda: callback(result))

    threading.Thread(target=target, daemon=True).start()


def verify_doctor_id(doctor_id: int):
    conn = get_connection()
    if not conn:
        return None
    cur = conn.cursor()
    try:
        cur.execute("SELECT doctor_id, full_name FROM doctors WHERE doctor_id = %s", (doctor_id,))
        return cur.fetchone()
    except Exception:
        return None
    finally:
        cur.close()
        conn.close()


def verify_staff(full_name: str, password: str):
    conn = get_connection()
    if not conn:
        return None
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT staff_id, full_name FROM staffs WHERE full_name = %s AND password = %s",
            (full_name, password),
        )
        return cur.fetchone()
    except Exception:
        return None
    finally:
        cur.close()
        conn.close()


def fetch_all_appointments():
    conn = get_connection()
    if not conn:
        return []
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT a.appointment_id, a.full_name, a.doctor_id, d.full_name,
                   a.date, a.time, a.status
            FROM appointments a
            LEFT JOIN doctors d ON a.doctor_id = d.doctor_id
            ORDER BY a.date DESC, a.time DESC
            """
        )
        return cur.fetchall()
    except Exception:
        return []
    finally:
        cur.close()
        conn.close()


def fetch_appointment_profile(appointment_id: int):
    conn = get_connection()
    if not conn:
        return None
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT appointment_id, full_name, doctor_id, date, time,
                   id_no, phone, gender, blood_type, birth_date, medical_history, status
            FROM appointments
            WHERE appointment_id = %s
            """,
            (appointment_id,),
        )
        return cur.fetchone()
    except Exception:
        return None
    finally:
        cur.close()
        conn.close()


def create_appointment_record(
    full_name: str,
    phone: str,
    gender: str,
    blood_type: str,
    id_no: str,
    birth_date: str,
    doctor_id: int,
    app_date: str,
    app_time: str,
    note: str = "",
    medical_history: str = "",
):
    conn = get_connection()
    if not conn:
        return False
    cur = conn.cursor()
    try:
        cur.execute("SELECT 1 FROM doctors WHERE doctor_id = %s", (doctor_id,))
        if not cur.fetchone():
            return False

        note = note.strip()
        medical_history = medical_history.strip()

        parts = []
        if medical_history:
            parts.append(f"Medical History:\n{medical_history}")
        if note:
            parts.append(f"Staff Note:\n{note}")

        payload = "\n\n".join(parts) if parts else None

        cur.execute(
            """
            INSERT INTO appointments
                (full_name, doctor_id, date, time, id_no, phone, gender, blood_type, birth_date, medical_history, status)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                full_name,
                doctor_id,
                app_date,
                app_time,
                id_no,
                phone,
                gender,
                blood_type,
                birth_date,
                payload,
                "waiting",
            ),
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def append_appointment_note(appointment_id: int, note: str, mark_completed: bool = False):
    note = note.strip()
    if not note:
        return False

    conn = get_connection()
    if not conn:
        return False
    cur = conn.cursor()
    try:
        cur.execute("SELECT medical_history FROM appointments WHERE appointment_id = %s", (appointment_id,))
        row = cur.fetchone()
        if not row:
            return False

        existing_text = (row[0] or "").rstrip()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        new_entry = f"[{timestamp}] Doctor Note:\n{note}"
        merged_text = new_entry if not existing_text else f"{existing_text}\n\n{new_entry}"

        if mark_completed:
            cur.execute(
                "UPDATE appointments SET medical_history = %s, status = %s WHERE appointment_id = %s",
                (merged_text, "completed", appointment_id),
            )
        else:
            cur.execute(
                "UPDATE appointments SET medical_history = %s WHERE appointment_id = %s",
                (merged_text, appointment_id),
            )

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def update_appointment_status(appointment_id: int, status: str):
    status = status_key(status)
    if status not in {"waiting", "in_progress", "completed", "cancelled"}:
        return False

    conn = get_connection()
    if not conn:
        return False
    cur = conn.cursor()
    try:
        cur.execute("SELECT status FROM appointments WHERE appointment_id = %s", (appointment_id,))
        row = cur.fetchone()
        if not row:
            return False
        if status_key(row[0]) == status:
            return True

        cur.execute("UPDATE appointments SET status = %s WHERE appointment_id = %s", (status, appointment_id))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


class LoginScreen(ctk.CTkFrame):
    def __init__(self, master, on_doctor_login, on_staff_login):
        super().__init__(master, fg_color=C_BG)
        self.on_doctor_login = on_doctor_login
        self.on_staff_login = on_staff_login
        self._build()

    def _build(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        center = ctk.CTkFrame(self, fg_color=C_BG)
        center.grid(row=0, column=0)

        logo = ctk.CTkLabel(center, text="🏥", font=("Segoe UI", 56))
        logo.pack(pady=(0, 4))
        ctk.CTkLabel(center, text="MedicalCore", font=FONT_TITLE, text_color=C_ACCENT).pack()
        ctk.CTkLabel(center, text="Hospital Management System", font=FONT_SUB, text_color=C_MUTED).pack(
            pady=(2, 32)
        )

        tab_bar = ctk.CTkFrame(center, fg_color=C_CARD, corner_radius=12)
        tab_bar.pack(fill="x", ipadx=4, ipady=4)

        self.tab_var = tk.StringVar(value="doctor")
        for text, val in [("Doctor Login", "doctor"), ("Staff Login", "staff")]:
            ctk.CTkRadioButton(
                tab_bar,
                text=text,
                variable=self.tab_var,
                value=val,
                command=self._switch_tab,
                fg_color=C_ACCENT,
                border_color=C_BORDER,
                font=FONT_LABEL,
                text_color=C_TEXT,
            ).pack(side="left", padx=16, pady=8)

        self.card = ctk.CTkFrame(
            center,
            fg_color=C_CARD,
            corner_radius=16,
            border_width=1,
            border_color=C_BORDER,
        )
        self.card.pack(fill="x", pady=18, ipadx=8, ipady=16)

        self._build_doctor_form()

    def _clear_card(self):
        for w in self.card.winfo_children():
            w.destroy()

    def _switch_tab(self):
        self._clear_card()
        if self.tab_var.get() == "doctor":
            self._build_doctor_form()
        else:
            self._build_staff_form()

    def _build_doctor_form(self):
        ctk.CTkLabel(self.card, text="Doctor ID", font=FONT_LABEL, text_color=C_MUTED).pack(
            anchor="w", padx=24, pady=(20, 2)
        )
        self.doctor_id_entry = ctk.CTkEntry(
            self.card,
            placeholder_text="Enter your doctor ID",
            height=44,
            font=FONT_LABEL,
            fg_color=C_SURFACE,
            border_color=C_BORDER,
            text_color=C_TEXT,
            corner_radius=10,
        )
        self.doctor_id_entry.pack(fill="x", padx=24)
        self.doctor_id_entry.bind("<Return>", lambda e: self._do_doctor_login())

        self.doctor_err = ctk.CTkLabel(self.card, text="", text_color=C_DANGER, font=FONT_SMALL)
        self.doctor_err.pack(pady=(4, 0))

        ctk.CTkButton(
            self.card,
            text="Login as Doctor",
            height=44,
            font=("Segoe UI", 13, "bold"),
            fg_color=C_ACCENT,
            hover_color="#3a6fd8",
            corner_radius=10,
            command=self._do_doctor_login,
        ).pack(fill="x", padx=24, pady=(12, 20))

    def _build_staff_form(self):
        ctk.CTkLabel(self.card, text="Full Name", font=FONT_LABEL, text_color=C_MUTED).pack(
            anchor="w", padx=24, pady=(20, 2)
        )
        self.staff_name_entry = ctk.CTkEntry(
            self.card,
            placeholder_text="Enter your full name",
            height=44,
            font=FONT_LABEL,
            fg_color=C_SURFACE,
            border_color=C_BORDER,
            text_color=C_TEXT,
            corner_radius=10,
        )
        self.staff_name_entry.pack(fill="x", padx=24)

        ctk.CTkLabel(self.card, text="Password", font=FONT_LABEL, text_color=C_MUTED).pack(
            anchor="w", padx=24, pady=(12, 2)
        )
        self.staff_pw_entry = ctk.CTkEntry(
            self.card,
            placeholder_text="Enter your password",
            show="•",
            height=44,
            font=FONT_LABEL,
            fg_color=C_SURFACE,
            border_color=C_BORDER,
            text_color=C_TEXT,
            corner_radius=10,
        )
        self.staff_pw_entry.pack(fill="x", padx=24)
        self.staff_pw_entry.bind("<Return>", lambda e: self._do_staff_login())

        self.staff_err = ctk.CTkLabel(self.card, text="", text_color=C_DANGER, font=FONT_SMALL)
        self.staff_err.pack(pady=(4, 0))

        ctk.CTkButton(
            self.card,
            text="Login as Staff",
            height=44,
            font=("Segoe UI", 13, "bold"),
            fg_color=C_ACCENT2,
            hover_color="#6344a8",
            corner_radius=10,
            command=self._do_staff_login,
        ).pack(fill="x", padx=24, pady=(12, 20))

    def _do_doctor_login(self):
        raw = self.doctor_id_entry.get().strip()
        if not raw.isdigit():
            self.doctor_err.configure(text="Doctor ID must be a number.", text_color=C_DANGER)
            return

        self.doctor_err.configure(text="Verifying...", text_color=C_ACCENT)

        def fetch():
            return verify_doctor_id(int(raw))

        def done(result):
            if result:
                self.on_doctor_login(result[0], result[1])
            else:
                self.doctor_err.configure(text="Doctor ID not found.", text_color=C_DANGER)

        run_in_thread(fetch, callback=done)

    def _do_staff_login(self):
        full_name = self.staff_name_entry.get().strip()
        password = self.staff_pw_entry.get()
        if not full_name or not password:
            self.staff_err.configure(text="Both fields are required.", text_color=C_DANGER)
            return

        self.staff_err.configure(text="Verifying...", text_color=C_ACCENT)

        def fetch():
            return verify_staff(full_name, password)

        def done(result):
            if result:
                self.on_staff_login(result[1])
            else:
                self.staff_err.configure(text="Invalid name or password.", text_color=C_DANGER)

        run_in_thread(fetch, callback=done)


class StaffDashboard(ctk.CTkFrame):
    def __init__(self, master, staff_name: str, on_logout):
        super().__init__(master, fg_color=C_BG)
        self.staff_name = staff_name
        self.on_logout = on_logout
        self.staff_api = StaffAuth()
        self._build()

    def _build(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        topbar = ctk.CTkFrame(self, fg_color=C_SURFACE, height=56, corner_radius=0)
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(topbar, text="🏥  MedicalCore", font=("Segoe UI", 16, "bold"), text_color=C_ACCENT).grid(
            row=0, column=0, padx=20, pady=12
        )
        ctk.CTkLabel(topbar, text=f"Staff Panel  •  {self.staff_name}", font=FONT_LABEL, text_color=C_MUTED).grid(
            row=0, column=1, padx=8
        )
        ctk.CTkButton(
            topbar,
            text="Logout",
            width=90,
            height=32,
            fg_color=C_DANGER,
            hover_color="#c45252",
            font=FONT_SMALL,
            corner_radius=8,
            command=self.on_logout,
        ).grid(row=0, column=2, padx=16)

        self.tabs = ctk.CTkTabview(
            self,
            fg_color=C_BG,
            segmented_button_fg_color=C_CARD,
            segmented_button_selected_color=C_ACCENT,
            segmented_button_unselected_color=C_CARD,
            segmented_button_selected_hover_color="#3a6fd8",
            text_color=C_TEXT,
        )
        self.tabs.grid(row=1, column=0, sticky="nsew", padx=16, pady=12)

        self.tabs.add("Patient Registration")
        self.tabs.add("Doctor Management")
        self.tabs.add("Appointments")

        self._build_patient_tab(self.tabs.tab("Patient Registration"))
        self._build_doctor_tab(self.tabs.tab("Doctor Management"))
        self._build_appointments_tab(self.tabs.tab("Appointments"))

    def _build_patient_tab(self, parent):
        parent.grid_columnconfigure((0, 1), weight=1)

        def lbl(row, col, text):
            ctk.CTkLabel(parent, text=text, font=FONT_LABEL, text_color=C_MUTED).grid(
                row=row, column=col, sticky="w", padx=(16, 4), pady=(10, 0)
            )

        def ent(row, col, ph="", span=1):
            e = ctk.CTkEntry(
                parent,
                placeholder_text=ph,
                height=40,
                fg_color=C_CARD,
                border_color=C_BORDER,
                text_color=C_TEXT,
                font=FONT_LABEL,
                corner_radius=8,
            )
            e.grid(row=row, column=col, columnspan=span, sticky="ew", padx=16, pady=(2, 0))
            return e

        def txt(row, col):
            t = ctk.CTkTextbox(
                parent,
                height=92,
                fg_color=C_CARD,
                text_color=C_TEXT,
                font=FONT_LABEL,
                border_color=C_BORDER,
                border_width=1,
                corner_radius=8,
            )
            t.grid(row=row, column=col, sticky="nsew", padx=16, pady=(2, 0))
            return t

        lbl(0, 0, "Full Name")
        lbl(0, 1, "National ID (id_no)")
        self.pr_name = ent(1, 0, "e.g. John Smith")
        self.pr_idno = ent(1, 1, "11-digit ID number")

        lbl(2, 0, "Phone")
        lbl(2, 1, "Gender")
        self.pr_phone = ent(3, 0, "e.g. +1 555 000 0000")
        self.pr_gender = ctk.CTkOptionMenu(
            parent,
            values=["Male", "Female", "Other"],
            fg_color=C_CARD,
            button_color=C_ACCENT,
            button_hover_color="#3a6fd8",
            dropdown_fg_color=C_CARD,
            text_color=C_TEXT,
            font=FONT_LABEL,
            dropdown_text_color=C_TEXT,
            height=40,
            corner_radius=8,
        )
        self.pr_gender.grid(row=3, column=1, sticky="ew", padx=16, pady=(2, 0))

        lbl(4, 0, "Blood Type")
        lbl(4, 1, "Birth Date (YYYY-MM-DD)")
        self.pr_blood = ctk.CTkOptionMenu(
            parent,
            values=["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
            fg_color=C_CARD,
            button_color=C_ACCENT,
            button_hover_color="#3a6fd8",
            dropdown_fg_color=C_CARD,
            text_color=C_TEXT,
            font=FONT_LABEL,
            dropdown_text_color=C_TEXT,
            height=40,
            corner_radius=8,
        )
        self.pr_blood.grid(row=5, column=0, sticky="ew", padx=16, pady=(2, 0))
        self.pr_birth = ent(5, 1, "YYYY-MM-DD")

        lbl(6, 0, "Doctor ID")
        lbl(6, 1, "Appointment Date (YYYY-MM-DD)")
        self.pr_docid = ent(7, 0, "Assigned doctor ID")
        self.pr_appdate = ent(7, 1, "YYYY-MM-DD")

        lbl(8, 0, "Appointment Time (HH:MM)")
        self.pr_apptime = ent(9, 0, "HH:MM")

        lbl(10, 0, "Initial Note")
        lbl(10, 1, "Medical History")
        self.pr_note = txt(11, 0)
        self.pr_history = txt(11, 1)

        self.pr_status = ctk.CTkLabel(parent, text="", font=FONT_SMALL)
        self.pr_status.grid(row=12, column=0, columnspan=2, pady=(8, 0))

        ctk.CTkButton(
            parent,
            text="Register Patient & Create Appointment",
            height=46,
            font=("Segoe UI", 13, "bold"),
            fg_color=C_ACCENT,
            hover_color="#3a6fd8",
            corner_radius=10,
            command=self._do_register_patient,
        ).grid(row=13, column=0, columnspan=2, sticky="ew", padx=16, pady=16)

    def _do_register_patient(self):
        fields = {
            "Full Name": self.pr_name.get().strip(),
            "National ID": self.pr_idno.get().strip(),
            "Phone": self.pr_phone.get().strip(),
            "Birth Date": self.pr_birth.get().strip(),
            "Doctor ID": self.pr_docid.get().strip(),
            "Appointment Date": self.pr_appdate.get().strip(),
            "Appointment Time": self.pr_apptime.get().strip(),
        }
        note = self.pr_note.get("1.0", "end").strip()
        medical_history = self.pr_history.get("1.0", "end").strip()

        for name, val in fields.items():
            if not val:
                self.pr_status.configure(text=f"'{name}' is required.", text_color=C_DANGER)
                return

        try:
            datetime.strptime(fields["Birth Date"], "%Y-%m-%d")
            datetime.strptime(fields["Appointment Date"], "%Y-%m-%d")
            datetime.strptime(fields["Appointment Time"], "%H:%M")
            int(fields["Doctor ID"])
        except ValueError as e:
            self.pr_status.configure(text=f"Format error: {e}", text_color=C_DANGER)
            return

        self.pr_status.configure(text="Registering...", text_color=C_ACCENT)

        def do():
            return create_appointment_record(
                fields["Full Name"],
                fields["Phone"],
                self.pr_gender.get(),
                self.pr_blood.get(),
                fields["National ID"],
                fields["Birth Date"],
                int(fields["Doctor ID"]),
                fields["Appointment Date"],
                fields["Appointment Time"],
                note=note,
                medical_history=medical_history,
            )

        def done(ok):
            if ok:
                self.pr_status.configure(text="Patient registered successfully.", text_color=C_SUCCESS)
                for e in [
                    self.pr_name,
                    self.pr_idno,
                    self.pr_phone,
                    self.pr_birth,
                    self.pr_docid,
                    self.pr_appdate,
                    self.pr_apptime,
                ]:
                    e.delete(0, "end")
                self.pr_note.delete("1.0", "end")
                self.pr_history.delete("1.0", "end")
                self._load_all_appointments()
            else:
                self.pr_status.configure(
                    text="Registration failed. Check doctor ID or duplicate entry.",
                    text_color=C_DANGER,
                )

        run_in_thread(do, callback=done)

    def _build_appointments_tab(self, parent):
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(parent, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(hdr, text="All Appointments", font=("Segoe UI", 14, "bold"), text_color=C_TEXT).grid(
            row=0, column=0, sticky="w"
        )
        ctk.CTkLabel(hdr, text="Filter:", font=FONT_SMALL, text_color=C_MUTED).grid(row=0, column=1, padx=(12, 4))

        self.sa_filter_var = tk.StringVar(value="All")
        self.sa_filter_menu = ctk.CTkOptionMenu(
            hdr,
            variable=self.sa_filter_var,
            values=FILTER_STATUS_VALUES,
            width=130,
            height=30,
            font=FONT_SMALL,
            fg_color=C_CARD,
            button_color=C_ACCENT,
            button_hover_color="#3a6fd8",
            dropdown_fg_color=C_CARD,
            text_color=C_TEXT,
            dropdown_text_color=C_TEXT,
            corner_radius=8,
            command=lambda _: self._apply_sa_filter(),
        )
        self.sa_filter_menu.grid(row=0, column=2, padx=(0, 8))
        self.sa_filter_menu.set("All")

        ctk.CTkButton(
            hdr,
            text="⟳ Refresh",
            width=90,
            height=30,
            fg_color=C_CARD,
            hover_color=C_BORDER,
            font=FONT_SMALL,
            corner_radius=8,
            command=self._load_all_appointments,
        ).grid(row=0, column=3, padx=(0, 8))

        ctk.CTkButton(
            hdr,
            text="Cancel Selected",
            width=130,
            height=30,
            fg_color=C_DANGER,
            hover_color="#c45252",
            font=FONT_SMALL,
            corner_radius=8,
            command=self._do_cancel_selected_appointment,
        ).grid(row=0, column=4)

        tv_frame = ctk.CTkFrame(parent, fg_color=C_CARD, corner_radius=12)
        tv_frame.grid(row=1, column=0, sticky="nsew")
        tv_frame.grid_rowconfigure(0, weight=1)
        tv_frame.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.configure(
            "StaffAppt.Treeview",
            background=C_CARD,
            fieldbackground=C_CARD,
            foreground=C_TEXT,
            rowheight=34,
            font=("Segoe UI", 11),
            borderwidth=0,
        )
        style.configure(
            "StaffAppt.Treeview.Heading",
            background=C_SURFACE,
            foreground=C_MUTED,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
        )
        style.map("StaffAppt.Treeview", background=[("selected", C_ACCENT)])

        self.sa_tree = ttk.Treeview(
            tv_frame,
            style="StaffAppt.Treeview",
            columns=("id", "patient", "doc_id", "doctor", "date", "time", "status"),
            show="headings",
            selectmode="browse",
        )

        for col, text, width in [
            ("id", "Appt. ID", 80),
            ("patient", "Patient", 190),
            ("doc_id", "Doc. ID", 70),
            ("doctor", "Doctor", 180),
            ("date", "Date", 120),
            ("time", "Time", 90),
            ("status", "Status", 120),
        ]:
            self.sa_tree.heading(col, text=text)
            self.sa_tree.column(col, width=width, anchor="center")

        vsb = ttk.Scrollbar(tv_frame, orient="vertical", command=self.sa_tree.yview)
        self.sa_tree.configure(yscrollcommand=vsb.set)
        self.sa_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        self._sa_all_rows = []
        self._load_all_appointments()

    def _load_all_appointments(self):
        def done(rows):
            self._sa_all_rows = rows or []
            self._apply_sa_filter()

        run_in_thread(fetch_all_appointments, callback=done)

    def _apply_sa_filter(self):
        chosen = status_key(self.sa_filter_var.get())
        self.sa_tree.delete(*self.sa_tree.get_children())

        for r in self._sa_all_rows:
            row_status = status_key(r[6])
            if chosen != "all" and row_status != chosen:
                continue

            self.sa_tree.insert(
                "",
                "end",
                values=(
                    r[0],
                    r[1],
                    r[2],
                    r[3] or "—",
                    str(r[4]),
                    str(r[5]),
                    status_label(r[6]).upper(),
                ),
            )

    def _do_cancel_selected_appointment(self):
        sel = self.sa_tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select an appointment to cancel.")
            return

        row = self.sa_tree.item(sel[0], "values")
        appointment_id = int(row[0])
        patient_name = row[1]
        current_status = status_key(row[6])

        if current_status == "cancelled":
            messagebox.showinfo("Already Cancelled", "This appointment is already cancelled.")
            return

        if not messagebox.askyesno(
            "Confirm Cancellation",
            f"Cancel appointment {appointment_id} for {patient_name}?",
        ):
            return

        def do():
            return update_appointment_status(appointment_id, "cancelled")

        def done(ok):
            if ok:
                self._load_all_appointments()
            else:
                messagebox.showerror("Error", "Could not cancel the appointment.")

        run_in_thread(do, callback=done)

    def _build_doctor_tab(self, parent):
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=0)

        form = ctk.CTkFrame(parent, fg_color=C_CARD, corner_radius=12, border_width=1, border_color=C_BORDER)
        form.grid(row=0, column=1, rowspan=2, sticky="ns", padx=(8, 0), pady=0)
        form.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(form, text="Add New Doctor", font=("Segoe UI", 14, "bold"), text_color=C_TEXT).grid(
            row=0, column=0, padx=20, pady=(16, 4)
        )
        make_separator(form).grid(row=1, column=0, sticky="ew", padx=12)

        def flbl(row, text):
            ctk.CTkLabel(form, text=text, font=FONT_SMALL, text_color=C_MUTED).grid(
                row=row, column=0, sticky="w", padx=16, pady=(8, 0)
            )

        def fent(row, ph=""):
            e = ctk.CTkEntry(
                form,
                placeholder_text=ph,
                height=37,
                width=220,
                fg_color=C_SURFACE,
                border_color=C_BORDER,
                text_color=C_TEXT,
                font=FONT_LABEL,
                corner_radius=8,
            )
            e.grid(row=row, column=0, padx=16, pady=(2, 0))
            return e

        flbl(2, "Doctor ID")
        self.add_doc_id = fent(3, "Numeric ID")
        flbl(4, "Full Name")
        self.add_doc_name = fent(5, "e.g. Dr. Jane Doe")
        flbl(6, "National ID (id_no)")
        self.add_doc_idno = fent(7, "11-digit ID")
        flbl(8, "Birth Date (YYYY-MM-DD)")
        self.add_doc_bd = fent(9, "YYYY-MM-DD")

        self.add_doc_status = ctk.CTkLabel(form, text="", font=FONT_SMALL)
        self.add_doc_status.grid(row=10, column=0, pady=(6, 0))

        ctk.CTkButton(
            form,
            text="Add Doctor",
            height=40,
            width=220,
            fg_color=C_SUCCESS,
            hover_color="#27a87a",
            font=("Segoe UI", 12, "bold"),
            text_color="#051a10",
            corner_radius=8,
            command=self._do_add_doctor,
        ).grid(row=11, column=0, padx=16, pady=(10, 20))

        list_hdr = ctk.CTkFrame(parent, fg_color="transparent")
        list_hdr.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=(0, 8))
        list_hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(list_hdr, text="Registered Doctors", font=("Segoe UI", 14, "bold"), text_color=C_TEXT).grid(
            row=0, column=0, sticky="w"
        )
        ctk.CTkButton(
            list_hdr,
            text="⟳ Refresh",
            width=90,
            height=30,
            fg_color=C_CARD,
            hover_color=C_BORDER,
            font=FONT_SMALL,
            corner_radius=8,
            command=self._load_doctors,
        ).grid(row=0, column=1, padx=(8, 0))
        ctk.CTkButton(
            list_hdr,
            text="Delete Selected",
            width=130,
            height=30,
            fg_color=C_DANGER,
            hover_color="#c45252",
            font=FONT_SMALL,
            corner_radius=8,
            command=self._do_delete_doctor,
        ).grid(row=0, column=2, padx=(8, 0))

        tv_frame = ctk.CTkFrame(parent, fg_color=C_CARD, corner_radius=12)
        tv_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        tv_frame.grid_rowconfigure(0, weight=1)
        tv_frame.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "MedDoc.Treeview",
            background=C_CARD,
            fieldbackground=C_CARD,
            foreground=C_TEXT,
            rowheight=34,
            font=("Segoe UI", 11),
            borderwidth=0,
        )
        style.configure(
            "MedDoc.Treeview.Heading",
            background=C_SURFACE,
            foreground=C_MUTED,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
        )
        style.map("MedDoc.Treeview", background=[("selected", C_ACCENT)])

        self.doc_tree = ttk.Treeview(
            tv_frame,
            style="MedDoc.Treeview",
            columns=("id", "name", "id_no", "birthdate"),
            show="headings",
            selectmode="browse",
        )

        for col, text, width in [
            ("id", "Doctor ID", 100),
            ("name", "Full Name", 220),
            ("id_no", "National ID", 160),
            ("birthdate", "Birth Date", 130),
        ]:
            self.doc_tree.heading(col, text=text)
            self.doc_tree.column(col, width=width, anchor="center")

        vsb = ttk.Scrollbar(tv_frame, orient="vertical", command=self.doc_tree.yview)
        self.doc_tree.configure(yscrollcommand=vsb.set)
        self.doc_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        self._load_doctors()

    def _load_doctors(self):
        def fetch():
            return self.staff_api.list_doctors()

        def done(rows):
            self.doc_tree.delete(*self.doc_tree.get_children())
            rows = rows or []
            for r in rows:
                self.doc_tree.insert("", "end", values=(r[0], r[1], r[3], r[2]))

        run_in_thread(fetch, callback=done)

    def _do_add_doctor(self):
        doc_id = self.add_doc_id.get().strip()
        full_name = self.add_doc_name.get().strip()
        id_no = self.add_doc_idno.get().strip()
        bd = self.add_doc_bd.get().strip()

        if not all([doc_id, full_name, id_no, bd]):
            self.add_doc_status.configure(text="All fields are required.", text_color=C_DANGER)
            return

        if not doc_id.isdigit():
            self.add_doc_status.configure(text="Doctor ID must be a number.", text_color=C_DANGER)
            return

        try:
            datetime.strptime(bd, "%Y-%m-%d")
        except ValueError:
            self.add_doc_status.configure(text="Birth date format: YYYY-MM-DD", text_color=C_DANGER)
            return

        self.add_doc_status.configure(text="Adding...", text_color=C_ACCENT)

        def do():
            return self.staff_api.add_doctor(int(doc_id), full_name, id_no, bd)

        def done(ok):
            if ok:
                self.add_doc_status.configure(text="Doctor added.", text_color=C_SUCCESS)
                for e in [self.add_doc_id, self.add_doc_name, self.add_doc_idno, self.add_doc_bd]:
                    e.delete(0, "end")
                self._load_doctors()
            else:
                self.add_doc_status.configure(text="Failed. ID may already exist.", text_color=C_DANGER)

        run_in_thread(do, callback=done)

    def _do_delete_doctor(self):
        sel = self.doc_tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a doctor to delete.")
            return

        row = self.doc_tree.item(sel[0], "values")
        doc_id = int(row[0])
        name = row[1]

        if not messagebox.askyesno("Confirm Delete", f"Permanently delete Dr. {name} (ID {doc_id})?"):
            return

        def do():
            return self.staff_api.delete_doctor(doc_id)

        def done(ok):
            if ok:
                self._load_doctors()
            else:
                messagebox.showerror("Error", "Could not delete doctor.")

        run_in_thread(do, callback=done)


class DiagnosisPopup(ctk.CTkToplevel):
    def __init__(self, master, appointment_row, doctor_api: DoctorAuth, on_change=None):
        super().__init__(master)
        self.doctor_api = doctor_api
        self.on_change = on_change
        self.a_fullname, self.appointment_id, self.birth_date, self.a_date, self.a_time, self.status = appointment_row
        self.title("Appointment Details - MedicalCore")
        self.geometry("560x750")
        self.configure(fg_color=C_BG)
        self.resizable(False, False)
        self.grab_set()
        self.status_var = tk.StringVar(value=status_label(self.status))
        self._build()
        self._load_patient()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=C_SURFACE, corner_radius=0, height=54)
        hdr.pack(fill="x")

        ctk.CTkLabel(hdr, text=f"👤  {self.a_fullname}", font=("Segoe UI", 15, "bold"), text_color=C_TEXT).pack(
            side="left", padx=20, pady=14
        )

        self.status_badge = ctk.CTkLabel(
            hdr,
            text=f"  {status_label(self.status).upper()}  ",
            fg_color=status_color(self.status),
            corner_radius=6,
            font=FONT_BADGE,
            text_color="#0a0a0a",
        )
        self.status_badge.pack(side="right", padx=20, pady=14)

        info = ctk.CTkFrame(self, fg_color=C_CARD, corner_radius=10)
        info.pack(fill="x", padx=16, pady=(12, 0))

        for label, value in [
            ("📅 Date", str(self.a_date)),
            ("🕐 Time", str(self.a_time)),
            ("🆔 Appt. ID", str(self.appointment_id)),
            ("🎂 DOB", str(self.birth_date)),
        ]:
            col = ctk.CTkFrame(info, fg_color="transparent")
            col.pack(side="left", expand=True, padx=12, pady=10)
            ctk.CTkLabel(col, text=label, font=FONT_SMALL, text_color=C_MUTED).pack()
            ctk.CTkLabel(col, text=value, font=("Segoe UI", 12, "bold"), text_color=C_TEXT).pack()

        make_separator(self, C_BORDER).pack(fill="x", padx=16, pady=10)

        ctk.CTkLabel(self, text="Patient Medical History", font=("Segoe UI", 13, "bold"), text_color=C_TEXT).pack(
            anchor="w", padx=20
        )

        self.history_box = ctk.CTkTextbox(
            self,
            height=148,
            fg_color=C_CARD,
            text_color=C_TEXT,
            font=FONT_MONO,
            border_color=C_BORDER,
            border_width=1,
            corner_radius=8,
            state="disabled",
        )
        self.history_box.pack(fill="x", padx=16, pady=(6, 0))

        make_separator(self, C_BORDER).pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(self, text="Appointment Status", font=("Segoe UI", 13, "bold"), text_color=C_TEXT).pack(
            anchor="w", padx=20
        )

        status_row = ctk.CTkFrame(self, fg_color="transparent")
        status_row.pack(fill="x", padx=16, pady=(6, 0))

        self.status_menu = ctk.CTkOptionMenu(
            status_row,
            variable=self.status_var,
            values=APPOINTMENT_STATUS_VALUES,
            fg_color=C_CARD,
            button_color=C_ACCENT,
            button_hover_color="#3a6fd8",
            dropdown_fg_color=C_CARD,
            text_color=C_TEXT,
            dropdown_text_color=C_TEXT,
            font=FONT_LABEL,
            height=40,
            corner_radius=8,
        )
        self.status_menu.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            status_row,
            text="Save Status",
            width=120,
            height=40,
            fg_color=C_ACCENT,
            hover_color="#3a6fd8",
            corner_radius=8,
            font=("Segoe UI", 12, "bold"),
            command=self._do_save_status,
        ).pack(side="left", padx=(8, 0))

        ctk.CTkButton(
            status_row,
            text="Cancel Appointment",
            width=150,
            height=40,
            fg_color=C_DANGER,
            hover_color="#c45252",
            corner_radius=8,
            font=("Segoe UI", 12, "bold"),
            command=self._do_cancel_appointment,
        ).pack(side="left", padx=(8, 0))

        make_separator(self, C_BORDER).pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(self, text="Add Diagnosis / Note", font=("Segoe UI", 13, "bold"), text_color=C_TEXT).pack(
            anchor="w", padx=20
        )

        self.diagnosis_box = ctk.CTkTextbox(
            self,
            height=108,
            fg_color=C_CARD,
            text_color=C_TEXT,
            font=FONT_LABEL,
            border_color=C_BORDER,
            border_width=1,
            corner_radius=8,
        )
        self.diagnosis_box.pack(fill="x", padx=16, pady=(6, 0))

        self.diag_status = ctk.CTkLabel(self, text="", font=FONT_SMALL)
        self.diag_status.pack(pady=(8, 0))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=14)
        btn_row.grid_columnconfigure(0, weight=1)
        btn_row.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            btn_row,
            text="Add Note",
            height=44,
            font=("Segoe UI", 13, "bold"),
            fg_color=C_ACCENT2,
            hover_color="#6344a8",
            text_color=C_TEXT,
            corner_radius=10,
            command=lambda: self._do_save_note(False),
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkButton(
            btn_row,
            text="Add Note & Mark Completed",
            height=44,
            font=("Segoe UI", 13, "bold"),
            fg_color=C_SUCCESS,
            hover_color="#27a87a",
            text_color="#051a10",
            corner_radius=10,
            command=lambda: self._do_save_note(True),
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def _set_status(self, status: str):
        self.status = status_key(status)
        self.status_var.set(status_label(self.status))
        self.status_badge.configure(
            text=f"  {status_label(self.status).upper()}  ",
            fg_color=status_color(self.status),
        )

    def _load_patient(self):
        def fetch():
            return fetch_appointment_profile(self.appointment_id)

        def done(profile):
            self.history_box.configure(state="normal")
            self.history_box.delete("1.0", "end")
            if profile:
                history = profile[10] if profile[10] else "(No history recorded)"
                self.history_box.insert("end", history)
            else:
                self.history_box.insert("end", "(Could not load patient record)")
            self.history_box.configure(state="disabled")

        run_in_thread(fetch, callback=done)

    def _notify_change(self):
        if callable(self.on_change):
            self.on_change()

    def _do_save_note(self, mark_completed: bool):
        text = self.diagnosis_box.get("1.0", "end").strip()
        if not text:
            self.diag_status.configure(text="Diagnosis note cannot be empty.", text_color=C_DANGER)
            return

        self.diag_status.configure(
            text="Saving and completing..." if mark_completed else "Saving note...",
            text_color=C_ACCENT,
        )

        def do():
            return append_appointment_note(self.appointment_id, text, mark_completed=mark_completed)

        def done(ok):
            if ok:
                if mark_completed:
                    self._set_status("completed")
                self.diagnosis_box.delete("1.0", "end")
                self.diag_status.configure(text="Saved successfully.", text_color=C_SUCCESS)
                self._load_patient()
                self._notify_change()
            else:
                self.diag_status.configure(text="Save failed.", text_color=C_DANGER)

        run_in_thread(do, callback=done)

    def _do_save_status(self):
        new_status = status_key(self.status_var.get())
        self.diag_status.configure(text="Updating status...", text_color=C_ACCENT)

        def do():
            return update_appointment_status(self.appointment_id, new_status)

        def done(ok):
            if ok:
                self._set_status(new_status)
                self.diag_status.configure(text="Status updated.", text_color=C_SUCCESS)
                self._notify_change()
            else:
                self.diag_status.configure(text="Status update failed.", text_color=C_DANGER)

        run_in_thread(do, callback=done)

    def _do_cancel_appointment(self):
        if status_key(self.status) == "cancelled":
            self.diag_status.configure(text="Appointment is already cancelled.", text_color=C_MUTED)
            return

        if not messagebox.askyesno("Confirm Cancellation", f"Cancel appointment {self.appointment_id}?"):
            return

        self.diag_status.configure(text="Cancelling appointment...", text_color=C_ACCENT)

        def do():
            return update_appointment_status(self.appointment_id, "cancelled")

        def done(ok):
            if ok:
                self._set_status("cancelled")
                self.diag_status.configure(text="Appointment cancelled.", text_color=C_SUCCESS)
                self._notify_change()
            else:
                self.diag_status.configure(text="Cancellation failed.", text_color=C_DANGER)

        run_in_thread(do, callback=done)


class DoctorDashboard(ctk.CTkFrame):
    def __init__(self, master, doctor_id: int, doctor_name: str, on_logout):
        super().__init__(master, fg_color=C_BG)
        self.doctor_id = doctor_id
        self.doctor_name = doctor_name
        self.on_logout = on_logout
        self.doctor_api = DoctorAuth()
        self._build()

    def _build(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        topbar = ctk.CTkFrame(self, fg_color=C_SURFACE, height=56, corner_radius=0)
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(topbar, text="🏥  MedicalCore", font=("Segoe UI", 16, "bold"), text_color=C_ACCENT).grid(
            row=0, column=0, padx=20, pady=12
        )
        ctk.CTkLabel(
            topbar,
            text=f"Dr. {self.doctor_name}  •  ID {self.doctor_id}",
            font=FONT_LABEL,
            text_color=C_MUTED,
        ).grid(row=0, column=1, padx=8)
        ctk.CTkButton(
            topbar,
            text="⟳ Refresh",
            width=90,
            height=32,
            fg_color=C_CARD,
            hover_color=C_BORDER,
            font=FONT_SMALL,
            corner_radius=8,
            command=self._load_appointments,
        ).grid(row=0, column=2, padx=8)
        ctk.CTkButton(
            topbar,
            text="Logout",
            width=90,
            height=32,
            fg_color=C_DANGER,
            hover_color="#c45252",
            font=FONT_SMALL,
            corner_radius=8,
            command=self.on_logout,
        ).grid(row=0, column=3, padx=16)

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=20, pady=16)
        content.grid_rowconfigure(2, weight=1)
        content.grid_columnconfigure(0, weight=1)

        self.card_total = self._stat_card(content, "Total", "—", C_ACCENT)
        self.card_waiting = self._stat_card(content, "Waiting", "—", "#f59e0b")
        self.card_progress = self._stat_card(content, "In Progress", "—", C_ACCENT2)
        self.card_done = self._stat_card(content, "Completed", "—", C_SUCCESS)

        for i, card in enumerate([self.card_total, self.card_waiting, self.card_progress, self.card_done]):
            content.grid_columnconfigure(i, weight=1)
            card.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0), pady=(0, 14))

        filter_bar = ctk.CTkFrame(content, fg_color="transparent")
        filter_bar.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(0, 6))
        filter_bar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            filter_bar,
            text="Double-click an appointment to view details, add notes, or manage status.",
            font=FONT_SMALL,
            text_color=C_MUTED,
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(filter_bar, text="Filter:", font=FONT_SMALL, text_color=C_MUTED).grid(
            row=0, column=2, padx=(16, 4)
        )

        self.appt_filter_var = tk.StringVar(value="All")
        appt_filter_menu = ctk.CTkOptionMenu(
            filter_bar,
            variable=self.appt_filter_var,
            values=FILTER_STATUS_VALUES,
            width=140,
            height=30,
            font=FONT_SMALL,
            fg_color=C_CARD,
            button_color=C_ACCENT,
            button_hover_color="#3a6fd8",
            dropdown_fg_color=C_CARD,
            text_color=C_TEXT,
            dropdown_text_color=C_TEXT,
            corner_radius=8,
            command=lambda _: self._apply_appt_filter(),
        )
        appt_filter_menu.grid(row=0, column=3)
        appt_filter_menu.set("All")

        tv_frame = ctk.CTkFrame(content, fg_color=C_CARD, corner_radius=12)
        tv_frame.grid(row=2, column=0, columnspan=4, sticky="nsew")
        tv_frame.grid_rowconfigure(0, weight=1)
        tv_frame.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "MedAppt.Treeview",
            background=C_CARD,
            fieldbackground=C_CARD,
            foreground=C_TEXT,
            rowheight=36,
            font=("Segoe UI", 11),
            borderwidth=0,
        )
        style.configure(
            "MedAppt.Treeview.Heading",
            background=C_SURFACE,
            foreground=C_MUTED,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
        )
        style.map("MedAppt.Treeview", background=[("selected", C_ACCENT2)])

        self.appt_tree = ttk.Treeview(
            tv_frame,
            style="MedAppt.Treeview",
            columns=("appt_id", "patient", "date", "time", "status"),
            show="headings",
            selectmode="browse",
        )

        for col, text, width in [
            ("appt_id", "Appt. ID", 90),
            ("patient", "Patient Name", 240),
            ("date", "Date", 130),
            ("time", "Time", 100),
            ("status", "Status", 130),
        ]:
            self.appt_tree.heading(col, text=text)
            self.appt_tree.column(col, width=width, anchor="center")

        vsb = ttk.Scrollbar(tv_frame, orient="vertical", command=self.appt_tree.yview)
        self.appt_tree.configure(yscrollcommand=vsb.set)
        self.appt_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        self.appt_tree.bind("<Double-1>", self._on_appt_double_click)
        self.appt_tree.bind("<Return>", self._on_appt_double_click)

        self._appt_rows = {}
        self._all_appt_rows = []
        self._load_appointments()

    def _stat_card(self, parent, label, value, color) -> ctk.CTkFrame:
        card = ctk.CTkFrame(parent, fg_color=C_CARD, corner_radius=12, border_width=1, border_color=C_BORDER)
        ctk.CTkLabel(card, text=label, font=FONT_SMALL, text_color=C_MUTED).pack(pady=(12, 2))
        val_lbl = ctk.CTkLabel(card, text=value, font=("Segoe UI", 26, "bold"), text_color=color)
        val_lbl.pack(pady=(0, 12))
        card._value_lbl = val_lbl
        return card

    def _load_appointments(self):
        def fetch():
            return self.doctor_api.list_appointments(self.doctor_id)

        def done(rows):
            self._all_appt_rows = rows or []
            counts = {"waiting": 0, "in_progress": 0, "completed": 0, "cancelled": 0}

            for row in self._all_appt_rows:
                s = status_key(row[5])
                if s in counts:
                    counts[s] += 1

            self.card_total._value_lbl.configure(text=str(len(self._all_appt_rows)))
            self.card_waiting._value_lbl.configure(text=str(counts["waiting"]))
            self.card_progress._value_lbl.configure(text=str(counts["in_progress"]))
            self.card_done._value_lbl.configure(text=str(counts["completed"]))
            self._apply_appt_filter()

        run_in_thread(fetch, callback=done)

    def _apply_appt_filter(self):
        chosen = status_key(self.appt_filter_var.get())
        self.appt_tree.delete(*self.appt_tree.get_children())
        self._appt_rows.clear()

        for row in self._all_appt_rows:
            full_name, appointment_id, birth_date, date, time, status = row
            if chosen != "all" and status_key(status) != chosen:
                continue

            iid = self.appt_tree.insert(
                "",
                "end",
                values=(appointment_id, full_name, str(date), str(time), status_label(status).upper()),
            )
            self._appt_rows[iid] = row

    def _on_appt_double_click(self, event=None):
        sel = self.appt_tree.selection()
        if not sel:
            return

        row = self._appt_rows.get(sel[0])
        if row:
            DiagnosisPopup(self, row, self.doctor_api, on_change=self._load_appointments)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MedicalCore - Hospital Management System")
        self.geometry("1100x720")
        self.minsize(860, 600)
        self.configure(fg_color=C_BG)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._active_frame = None
        self._show_login()

    def _swap(self, frame: ctk.CTkFrame):
        if self._active_frame:
            self._active_frame.grid_forget()
            self._active_frame.destroy()
        self._active_frame = frame
        frame.grid(row=0, column=0, sticky="nsew")

    def _show_login(self):
        self._swap(
            LoginScreen(
                self,
                on_doctor_login=self._on_doctor_login,
                on_staff_login=self._on_staff_login,
            )
        )

    def _on_doctor_login(self, doctor_id: int, doctor_name: str):
        self._swap(
            DoctorDashboard(
                self,
                doctor_id=doctor_id,
                doctor_name=doctor_name,
                on_logout=self._show_login,
            )
        )

    def _on_staff_login(self, staff_name: str):
        self._swap(StaffDashboard(self, staff_name=staff_name, on_logout=self._show_login))


if __name__ == "__main__":
    if not check_internet():
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Internet Error",
            "Internet connection not detected.\nPlease check your network and try again."
        )
        root.destroy()
    else:
        app = App()
        app.mainloop()