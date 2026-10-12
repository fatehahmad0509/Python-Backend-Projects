# Main GUI module for RepairHub.
# Built with CustomTkinter and standard Tkinter.
# Uses a background ThreadPoolExecutor for all database operations
# so the UI thread is never blocked.

from __future__ import annotations
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor

import customtkinter as ctk
from tkinter import ttk, messagebox

from database.db import session_scope
from services.services import (
    CustomerService, DeviceService, JobService,
    PaymentService, DashboardService,
)
from models.models import VALID_TRANSITIONS
from utils.logger import logger

# ── COLOR PALETTE ────────────────────────────────────────────────────────────
C = {
    "bg":       "#0d1526",  # main background
    "bg2":      "#1a2035",  # secondary background
    "bg3":      "#1e2a45",  # tertiary background / button hover
    "sidebar":  "#090e1a",  # sidebar background
    "card":     "#131d33",  # dashboard stat cards
    "accent":   "#1565C0",  # primary accent (blue)
    "acc_hov":  "#1976D2",  # accent hover state
    "acc_lite": "#4fc3f7",  # light accent for headings
    "txt":      "#e8eaf6",  # primary text
    "txt2":     "#78909c",  # secondary / muted text
    "ok":       "#43a047",  # success / green
    "warn":     "#f57c00",  # warning / orange
    "err":      "#e53935",  # error / red
    "border":   "#243050",  # border / separator
}

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Global reference to the root window (used by background threads for after() calls)
_root: ctk.CTk | None = None

# Thread pool for all database I/O — keeps the UI responsive
_executor = ThreadPoolExecutor(max_workers=6, thread_name_prefix="RH")


def _run(fn, ok_cb=None, err_cb=None):
    """Submit fn() to the thread pool. On completion schedule ok_cb or err_cb on the main thread."""
    def _task():
        try:
            res = fn()
            if ok_cb:
                root = _root
                if root:
                    try:
                        root.after(0, lambda: ok_cb(res))
                    except tk.TclError:
                        pass
        except Exception as exc:
            logger.error(f"Thread error: {exc}", exc_info=True)
            if err_cb:
                root = _root
                if root:
                    try:
                        root.after(0, lambda e=exc: err_cb(str(e)))
                    except tk.TclError:
                        pass
    _executor.submit(_task)


def _style_tree():
    """Apply a custom dark theme to all Treeview widgets."""
    s = ttk.Style(); s.theme_use("default")
    s.configure("RH.Treeview",
        background=C["bg2"], foreground=C["txt"], fieldbackground=C["bg2"],
        rowheight=29, font=("Segoe UI", 10), borderwidth=0)
    s.configure("RH.Treeview.Heading",
        background=C["bg"], foreground=C["acc_lite"],
        font=("Segoe UI", 10, "bold"), relief="flat")
    s.map("RH.Treeview",
          background=[("selected", C["accent"])],
          foreground=[("selected", "white")])


def _make_tree(parent, cols, heads, widths=None, stretch_cols=None):
    """Create a styled Treeview with a vertical scrollbar inside a wrapper frame."""
    wrap = ctk.CTkFrame(parent, fg_color=C["bg2"], corner_radius=8)
    tree = ttk.Treeview(wrap, columns=cols, show="headings",
                    style="RH.Treeview", selectmode="browse")
    vsb = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    for i, (c, h) in enumerate(zip(cols, heads)):
        tree.heading(c, text=h, anchor="center")
        stretch = stretch_cols and i in stretch_cols
        tree.column(c, width=widths[i] if widths else 100, minwidth=50, stretch=stretch, anchor="center")
    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    wrap.grid_rowconfigure(0, weight=1); wrap.grid_columnconfigure(0, weight=1)
    # ── SÜRÜKLEMEYİ KAPAT ──
    def _block_resize(event):
        if tree.identify_region(event.x, event.y) in ("heading", "separator"):
            return "break"
    tree.bind("<ButtonPress-1>", _block_resize, add="+")
    return wrap, tree


# ── REUSABLE WIDGET HELPERS ──────────────────────────────────────────────────

class StatCard(ctk.CTkFrame):
    """A small dashboard card displaying a title label and a numeric value."""

    def __init__(self, parent, title, value, color):
        super().__init__(parent, fg_color=C["card"], corner_radius=12)
        ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=11),
                    text_color=C["txt2"]).pack(pady=(14,3), padx=12)
        self._lbl = ctk.CTkLabel(self, text=str(value),
                    font=ctk.CTkFont(size=26, weight="bold"),
                    text_color=color)
        self._lbl.pack(pady=(0,14), padx=12)

    def set(self, v):
        """Update the displayed value."""
        self._lbl.configure(text=str(v))


def _lbl(parent, text, size=12, bold=False, color=None, **kw):
    """Shorthand factory for a CTkLabel with common styling."""
    return ctk.CTkLabel(parent, text=text, text_color=color or C["txt2"],
                    font=ctk.CTkFont(size=size, weight="bold" if bold else "normal"), **kw)

def _btn(parent, text, cmd, color=None, w=None, **kw):
    """Shorthand factory for a styled CTkButton."""
    return ctk.CTkButton(parent, text=text, command=cmd, width=w or 120,
                    fg_color=color or C["accent"], hover_color=C["acc_hov"],
                    text_color="white", font=ctk.CTkFont(size=12), **kw)

def _entry(parent, **kw):
    """Shorthand factory for a styled CTkEntry."""
    return ctk.CTkEntry(parent, fg_color=C["bg2"], border_color=C["border"],
                    text_color=C["txt"], **kw)

def _textbox(parent, height=80, **kw):
    """Shorthand factory for a styled CTkTextbox."""
    return ctk.CTkTextbox(parent, height=height, fg_color=C["bg2"],
                    border_color=C["border"], text_color=C["txt"], **kw)


# ── DIALOG BASE ──────────────────────────────────────────────────────────────

class _BaseDialog(ctk.CTkToplevel):
    """Base class for modal dialog windows."""

    def __init__(self, parent, title, w=460, h=500):
        super().__init__(parent)
        self.title(title)
        self.geometry(f"{w}x{h}")
        self.configure(fg_color=C["bg"])
        self.grab_set()          # Make modal
        self.resizable(False, False)


# ── SPECIFIC DIALOGS ─────────────────────────────────────────────────────────

class CustomerDialog(_BaseDialog):
    """Dialog for creating or editing a customer record."""

    def __init__(self, parent, customer=None, on_save=None):
        super().__init__(parent, "New Customer" if not customer else "Edit Customer", 440, 420)
        self._c = customer; self._cb = on_save; self._build()

    def _build(self):
        title = "Edit Customer" if self._c else "New Customer"
        _lbl(self, title, 15, bold=True, color=C["acc_lite"]).pack(pady=(18,10))
        f = ctk.CTkFrame(self, fg_color="transparent"); f.pack(fill="x", padx=28)
        self._e: dict = {}
        for lbl, key in [("Full Name", "name"), ("Phone", "phone"),
                         ("Email", "email"), ("Address", "address")]:
            _lbl(f, lbl).pack(anchor="w", pady=(7,1))
            e = _entry(f); e.pack(fill="x"); self._e[key] = e
        if self._c:
            for k in ("name","phone","email","address"):
                self._e[k].insert(0, getattr(self._c, k) or "")
        bf = ctk.CTkFrame(self, fg_color="transparent"); bf.pack(fill="x", padx=28, pady=16)
        _btn(bf, "✓ Save",   self._save,    color=C["ok"],  w=100).pack(side="left", padx=4)
        _btn(bf, "✕ Cancel", self.destroy,  color=C["err"], w=90).pack(side="left", padx=4)

    def _save(self):
        data = {k: e.get().strip() for k, e in self._e.items()}
        def fn():
            with session_scope() as s:
                svc = CustomerService(s)
                if self._c:
                    return svc.update(self._c.id, **data)
                return svc.create(**data)
        def _ok(_):
            if self._cb: self._cb()
            self.destroy()
        _run(fn, ok_cb=_ok, err_cb=lambda e: messagebox.showerror("Error", e, parent=self))


class DeviceDialog(_BaseDialog):
    """Dialog for creating or editing a device record."""

    def __init__(self, parent, device=None, on_save=None):
        super().__init__(parent, "New Device" if not device else "Edit Device", 460, 580)
        self._d = device; self._cb = on_save; self._build()

    def _build(self):
        title = "Edit Device" if self._d else "New Device"
        _lbl(self, title, 15, bold=True, color=C["acc_lite"]).pack(pady=(18,10))
        f = ctk.CTkFrame(self, fg_color="transparent"); f.pack(fill="x", padx=28)
        self._e: dict = {}
        fields = [
            ("Customer ID", "customer_id"), ("Brand", "brand"), ("Model", "model"),
            ("Serial No", "serial_no"), ("IMEI", "imei"),
        ]
        for lbl, key in fields:
            _lbl(f, lbl).pack(anchor="w", pady=(7,1))
            e = _entry(f); e.pack(fill="x"); self._e[key] = e
        _lbl(f, "Problem Description").pack(anchor="w", pady=(7,1))
        tb = _textbox(f, 75); tb.pack(fill="x"); self._e["problem_desc"] = tb
        if self._d:
            for k in ("brand","model","serial_no","imei"):
                self._e[k].insert(0, getattr(self._d, k) or "")
            self._e["customer_id"].insert(0, str(self._d.customer_id))
            self._e["problem_desc"].insert("1.0", self._d.problem_desc or "")
        bf = ctk.CTkFrame(self, fg_color="transparent"); bf.pack(fill="x", padx=28, pady=14)
        _btn(bf, "✓ Save",   self._save,   color=C["ok"],  w=100).pack(side="left", padx=4)
        _btn(bf, "✕ Cancel", self.destroy, color=C["err"], w=90).pack(side="left", padx=4)

    def _save(self):
        try:
            cid = int(self._e["customer_id"].get().strip())
        except ValueError:
            messagebox.showwarning("Warning", "Customer ID must be a number.", parent=self); return
        kwargs = {k: self._e[k].get().strip() for k in ("brand","model","serial_no","imei")}
        kwargs["problem_desc"] = self._e["problem_desc"].get("1.0","end").strip()
        def fn():
            with session_scope() as s:
                svc = DeviceService(s)
                if self._d:
                    return svc.update(self._d.id, **kwargs)
                return svc.create(cid, **kwargs)
        def _ok(_):
            if self._cb: self._cb()
            self.destroy()
        _run(fn, ok_cb=_ok, err_cb=lambda e: messagebox.showerror("Error", e, parent=self))


class JobDialog(_BaseDialog):
    """Dialog for creating or editing a work order (job)."""

    def __init__(self, parent, job=None, on_save=None):
        super().__init__(parent, "New Work Order" if not job else "Edit Work Order", 440, 520)
        self._j = job; self._cb = on_save; self._build()

    def _build(self):
        title = "Edit Work Order" if self._j else "New Work Order"
        _lbl(self, title, 15, bold=True, color=C["acc_lite"]).pack(pady=(18,10))
        f = ctk.CTkFrame(self, fg_color="transparent"); f.pack(fill="x", padx=28)
        self._e: dict = {}
        if not self._j:
            for lbl, key in [("Device ID","device_id"),("Customer ID","customer_id")]:
                _lbl(f, lbl).pack(anchor="w", pady=(7,1))
                e = _entry(f); e.pack(fill="x"); self._e[key] = e
        _lbl(f, "Technician").pack(anchor="w", pady=(7,1))
        te = _entry(f); te.pack(fill="x"); self._e["technician"] = te
        _lbl(f, "Notes").pack(anchor="w", pady=(7,1))
        tb = _textbox(f, 80); tb.pack(fill="x"); self._e["notes"] = tb
        if self._j:
            self._e["technician"].insert(0, self._j.technician or "")
            self._e["notes"].insert("1.0", self._j.notes or "")
        bf = ctk.CTkFrame(self, fg_color="transparent"); bf.pack(fill="x", padx=28, pady=14)
        _btn(bf, "✓ Save",   self._save,   color=C["ok"],  w=100).pack(side="left", padx=4)
        _btn(bf, "✕ Cancel", self.destroy, color=C["err"], w=90).pack(side="left", padx=4)

    def _save(self):
        tech  = self._e["technician"].get().strip()
        notes = self._e["notes"].get("1.0","end").strip()
        def fn():
            with session_scope() as s:
                svc = JobService(s)
                if self._j:
                    return svc.update(self._j.id, notes=notes, technician=tech)
                did = int(self._e["device_id"].get().strip())
                cid = int(self._e["customer_id"].get().strip())
                return svc.create(did, cid, notes, tech)
        def _ok(_):
            if self._cb: self._cb()
            self.destroy()
        _run(fn, ok_cb=_ok, err_cb=lambda e: messagebox.showerror("Error", e, parent=self))


class StatusDialog(_BaseDialog):
    """Dialog for changing the status of a work order."""

    def __init__(self, parent, job_id, current_status, on_save=None):
        super().__init__(parent, f"Change Status — Job #{job_id}", 380, 260)
        self._jid = job_id; self._cur = current_status; self._cb = on_save; self._build()

    def _build(self):
        _lbl(self, f"Job #{self._jid} — Current: {self._cur}", 13, bold=True,
             color=C["acc_lite"]).pack(pady=(18,10))
        options = VALID_TRANSITIONS.get(self._cur, [])
        if not options:
            _lbl(self, "No further transitions available for this status.").pack(pady=20)
            _btn(self, "Close", self.destroy, color=C["bg2"], w=90).pack()
            return
        _lbl(self, "New Status:").pack(anchor="w", padx=28, pady=(0,4))
        self._var = ctk.StringVar(value=options[0])
        ctk.CTkOptionMenu(self, values=options, variable=self._var,
                    fg_color=C["bg2"], button_color=C["accent"]).pack(padx=28, fill="x")
        bf = ctk.CTkFrame(self, fg_color="transparent"); bf.pack(fill="x", padx=28, pady=16)
        _btn(bf, "✓ Apply",  self._apply,  color=C["ok"],  w=100).pack(side="left", padx=4)
        _btn(bf, "✕ Cancel", self.destroy, color=C["err"], w=90).pack(side="left", padx=4)

    def _apply(self):
        new_status = self._var.get()
        def fn():
            with session_scope() as s:
                return JobService(s).change_status(self._jid, new_status)
        def _ok(_):
            if self._cb: self._cb()
            self.destroy()
        _run(fn, ok_cb=_ok, err_cb=lambda e: messagebox.showerror("Error", e, parent=self))


class LogDialog(_BaseDialog):
    """Dialog displaying the full status change history for a work order."""

    def __init__(self, parent, job_id):
        super().__init__(parent, f"Status History — Job #{job_id}", 680, 380)
        self._jid = job_id; self._build(); self._load()

    def _build(self):
        _lbl(self, "Status History", 15, bold=True, color=C["acc_lite"]).pack(pady=(14,8))
        wrap, self._tree = _make_tree(self,
            cols=("id","prev","new","source","ts"),
            heads=("ID","Previous","New Status","Action Source","Timestamp"),
            widths=(45,150,150,175,175),
            stretch_cols={2,3})
        wrap.pack(fill="both", expand=True, padx=14, pady=4)
        _btn(self, "Close", self.destroy, color=C["bg2"], w=90).pack(pady=10)

    def _load(self):
        def fn():
            with session_scope() as s:
                return JobService(s).get_status_log(self._jid)
        def show(logs):
            self._tree.delete(*self._tree.get_children())
            for lg in logs:
                self._tree.insert("","end", values=(
                    lg.id, lg.prev_status or "—", lg.new_status, lg.action_source or "—",
                    lg.timestamp.strftime("%d.%m.%Y %H:%M:%S") if lg.timestamp else ""))
        _run(fn, ok_cb=show, err_cb=lambda e: messagebox.showerror("Error", e, parent=self))


class HistoryDialog(_BaseDialog):
    """Dialog displaying all work orders associated with a specific customer."""

    def __init__(self, parent, customer_id):
        super().__init__(parent, "Customer Job History", 680, 420)
        self._cid = customer_id; self._build(); self._load()

    def _build(self):
        _lbl(self, "Job History", 15, bold=True, color=C["acc_lite"]).pack(pady=(14,8))
        wrap, self._tree = _make_tree(self,
            cols=("id","device","status","tech","date"),
            heads=("ID","Device","Status","Technician","Date"),
            widths=(45,210,140,130,130),
            stretch_cols={1})
        wrap.pack(fill="both", expand=True, padx=14, pady=4)
        _btn(self, "Close", self.destroy, color=C["bg2"], w=90).pack(pady=10)

    def _load(self):
        def fn():
            with session_scope() as s:
                jobs = JobService(s).get_by_customer(self._cid)
                return [(j.id,
                         f"{j.device.brand} {j.device.model}" if j.device else "—",
                         j.status, j.technician or "—", j.created_at) for j in jobs]
        def show(rows):
            self._tree.delete(*self._tree.get_children())
            for jid, dev, status, tech, created in rows:
                self._tree.insert("","end", values=(
                    jid, dev, status, tech,
                    created.strftime("%d.%m.%Y") if created else ""))
        _run(fn, ok_cb=show, err_cb=lambda e: messagebox.showerror("Error", e, parent=self))


class PaymentDialog(_BaseDialog):
    """Dialog for creating, updating, or partially paying a job's payment record."""

    def __init__(self, parent, job_id, payment=None, on_save=None):
        super().__init__(parent, f"Job #{job_id} — Payment", 430, 430)
        self._jid = job_id; self._p = payment; self._cb = on_save; self._build()

    def _build(self):
        _lbl(self, f"Payment — Job #{self._jid}", 15, bold=True, color=C["acc_lite"]).pack(pady=(18,10))
        f = ctk.CTkFrame(self, fg_color="transparent"); f.pack(fill="x", padx=28)
        self._e: dict = {}
        for lbl, key in [("Labor Cost","labor_cost"), ("Parts Cost","parts_cost"),
                         ("Paid Amount","paid_amount")]:
            _lbl(f, lbl).pack(anchor="w", pady=(7,1))
            e = _entry(f); e.pack(fill="x"); self._e[key] = e
        _lbl(f, "Notes").pack(anchor="w", pady=(7,1))
        tb = _textbox(f, 65); tb.pack(fill="x"); self._e["notes"] = tb
        if self._p:
            for field in ("labor_cost", "parts_cost", "paid_amount"):
                self._e[field].insert(0, str(getattr(self._p, field)))
            self._e["notes"].insert("1.0", self._p.notes or "")
        else:
            for k in ["labor_cost","parts_cost","paid_amount"]: self._e[k].insert(0,"0")
        self._total_lbl = _lbl(f, "Total: 0.00", 13, bold=True, color=C["ok"])
        self._total_lbl.pack(anchor="w", pady=(8,0))
        for k in ["labor_cost","parts_cost"]:
            self._e[k].bind("<KeyRelease>", lambda _: self._recalc())
        self._recalc()
        bf = ctk.CTkFrame(self, fg_color="transparent"); bf.pack(fill="x", padx=28, pady=14)
        _btn(bf, "✓ Save",      self._save,    color=C["ok"],     w=110).pack(side="left", padx=4)
        if self._p:
            _btn(bf, "💳 Partial", self._partial, color="#7b1fa2",  w=120).pack(side="left", padx=4)
        _btn(bf, "✕ Cancel",   self.destroy,  color=C["err"],    w=90).pack(side="left", padx=4)

    def _recalc(self):
        try:
            t = float(self._e["labor_cost"].get() or 0) + float(self._e["parts_cost"].get() or 0)
            self._total_lbl.configure(text=f"Total: {t:.2f}")
        except ValueError:
            self._total_lbl.configure(text="⚠ Invalid input")

    def _save(self):
        try:
            lc = float(self._e["labor_cost"].get() or 0)
            pc = float(self._e["parts_cost"].get() or 0)
            pa = float(self._e["paid_amount"].get() or 0)
        except ValueError:
            messagebox.showwarning("Warning", "Please enter numeric values.", parent=self); return
        notes = self._e["notes"].get("1.0","end").strip()
        def fn():
            with session_scope() as s:
                return PaymentService(s).create_or_update(self._jid, lc, pc, pa, notes)
        def _ok(_):
            if self._cb: self._cb()
            self.destroy()
        _run(fn, ok_cb=_ok, err_cb=lambda e: messagebox.showerror("Error", e, parent=self))

    def _partial(self):
        top = ctk.CTkToplevel(self); top.title("Partial Payment")
        top.geometry("280x180"); top.configure(fg_color=C["bg"]); top.grab_set()
        _lbl(top, "Amount:").pack(pady=(20,5))
        ae = _entry(top); ae.pack(padx=30, fill="x")
        def do():
            try: amt = float(ae.get())
            except ValueError:
                messagebox.showwarning("Warning", "Enter a valid amount.", parent=top); return
            def fn():
                with session_scope() as s:
                    return PaymentService(s).add_partial(self._jid, amt)
            def _ok(_):
                if self._cb: self._cb()
                top.destroy(); self.destroy()
            _run(fn, ok_cb=_ok, err_cb=lambda e: messagebox.showerror("Error", e, parent=top))
        _btn(top, "Pay", do, color=C["ok"], w=100).pack(pady=14)


# ── PAGE BASE ────────────────────────────────────────────────────────────────

class _PageBase(ctk.CTkFrame):
    """Base class for all main content pages."""

    def __init__(self, parent):
        super().__init__(parent, fg_color=C["bg"], corner_radius=0)

    def _header(self, title):
        row = ctk.CTkFrame(self, fg_color="transparent"); row.pack(fill="x", padx=22, pady=(22,8))
        _lbl(row, title, 20, bold=True, color=C["acc_lite"]).pack(side="left")
        return row

    def _status_bar(self):
        lbl = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=11), text_color=C["txt2"])
        lbl.pack(pady=(0,6))
        return lbl

    def _sel_id(self, tree, warn=True):
        sel = tree.selection()
        if not sel:
            if warn: messagebox.showwarning("Warning", "Please select a row first.")
            return None
        return int(sel[0])


# ── CUSTOMERS PAGE ───────────────────────────────────────────────────────────

class CustomersPage(_PageBase):
    """Displays the full customer list with search, add, edit, delete, and history."""

    def __init__(self, parent):
        super().__init__(parent); self._build(); self.refresh()

    def _build(self):
        hdr = self._header("👤  CUSTOMERS")
        self._sv = ctk.StringVar()
        se = ctk.CTkEntry(hdr, textvariable=self._sv, placeholder_text="🔍 Name, phone...",
                    width=260, fg_color=C["bg2"], border_color=C["border"])
        se.pack(side="left", padx=16); se.bind("<KeyRelease>", lambda _: self._search())
        bf = ctk.CTkFrame(hdr, fg_color="transparent"); bf.pack(side="right")
        for txt, cmd, col, w in [
            ("➕ New",      self._add,     C["ok"],     90),
            ("✏️ Edit",    self._edit,    C["accent"], 100),
            ("🗑️ Delete",  self._delete,  C["err"],    80),
            ("📋 History",  self._history, C["bg3"],   100),
            ("⟳",           self.refresh,  C["bg3"],   38),
        ]:
            _btn(bf, txt, cmd, col, w).pack(side="left", padx=2)
        wrap, self._tree = _make_tree(self,
            cols=("id","name","phone","email","addr","date"),
            heads=("ID","Full Name","Phone","Email","Address","Registered"),
            widths=(45,180,130,180,210,140),
            stretch_cols={1,3,4})
        wrap.pack(fill="both", expand=True, padx=22, pady=(0,4))
        self._sl = self._status_bar()

    def refresh(self):
        def fn():
            with session_scope() as s:
                rows = CustomerService(s).get_all()
                return [(c.id, c.name, c.phone, c.email or "", c.address or "", c.created_at) for c in rows]
        _run(fn, ok_cb=self._fill, err_cb=lambda e: messagebox.showerror("Error", e))

    def _search(self):
        q = self._sv.get().strip()
        if not q: self.refresh(); return
        def fn():
            with session_scope() as s:
                rows = CustomerService(s).search(q)
                return [(c.id, c.name, c.phone, c.email or "", c.address or "", c.created_at) for c in rows]
        _run(fn, ok_cb=self._fill)

    def _fill(self, rows):
        self._tree.delete(*self._tree.get_children())
        for cid, name, phone, email, addr, created in rows:
            self._tree.insert("","end", iid=str(cid), values=(
                cid, name, phone, email, addr[:55],
                created.strftime("%d.%m.%Y %H:%M") if created else ""))
        self._sl.configure(text=f"Total: {len(rows)} customers")

    def _add(self):    CustomerDialog(self, on_save=self.refresh)
    def _edit(self):
        cid = self._sel_id(self._tree)
        if not cid: return
        def fn():
            with session_scope() as s:
                return CustomerService(s).get_by_id(cid)
        _run(fn, ok_cb=lambda c: CustomerDialog(self, c, self.refresh) if c else None)

    def _delete(self):
        cid = self._sel_id(self._tree)
        if not cid: return
        if not messagebox.askyesno("Confirm", "Delete this customer and all related data?", parent=self): return
        def fn():
            with session_scope() as s:
                CustomerService(s).delete(cid)
        _run(fn, ok_cb=lambda _: self.refresh(), err_cb=lambda e: messagebox.showerror("Error", e))

    def _history(self):
        cid = self._sel_id(self._tree)
        if cid: HistoryDialog(self, cid)


# ── DEVICES PAGE ─────────────────────────────────────────────────────────────

class DevicesPage(_PageBase):
    """Displays all devices with add, edit, and delete actions."""

    def __init__(self, parent):
        super().__init__(parent); self._build(); self.refresh()

    def _build(self):
        hdr = self._header("💻  DEVICES")
        info = ctk.CTkFrame(self, fg_color=C["bg3"], corner_radius=6)
        info.pack(fill="x", padx=22, pady=(0,4))
        _lbl(info, "💡  To add a device, find the Customer ID on the Customers page.",
             11, color=C["acc_lite"]).pack(anchor="w", padx=10, pady=5)
        bf = ctk.CTkFrame(hdr, fg_color="transparent"); bf.pack(side="right")
        for txt, cmd, col, w in [
            ("➕ New",     self._add,    C["ok"],     90),
            ("✏️ Edit",   self._edit,   C["accent"], 100),
            ("🗑️ Delete", self._delete, C["err"],    80),
            ("⟳",          self.refresh, C["bg3"],   38),
        ]:
            _btn(bf, txt, cmd, col, w).pack(side="left", padx=2)
        wrap, self._tree = _make_tree(self,
            cols=("id","cid","cust","brand","model","serial","imei","problem","date"),
            heads=("ID","Cust. ID","Customer","Brand","Model","Serial No","IMEI","Problem","Entry Date"),
            widths=(45,80,140,100,120,110,120,190,110),
            stretch_cols={2,3,4,7})
        wrap.pack(fill="both", expand=True, padx=22, pady=(0,4))
        self._sl = self._status_bar()

    def refresh(self):
        def fn():
            with session_scope() as s:
                rows = DeviceService(s).get_all()
                return [(d.id, d.customer_id, d.customer.name if d.customer else "—",
                         d.brand or "", d.model or "", d.serial_no or "", d.imei or "",
                         d.problem_desc or "", d.entry_date) for d in rows]
        _run(fn, ok_cb=self._fill, err_cb=lambda e: messagebox.showerror("Error", e))

    def _fill(self, rows):
        self._tree.delete(*self._tree.get_children())
        for did, cid, cn, brand, model, serial, imei, problem, date in rows:
            self._tree.insert("","end", iid=str(did), values=(
                did, cid, cn, brand, model, serial, imei,
                problem[:55],
                date.strftime("%d.%m.%Y") if date else ""))
        self._sl.configure(text=f"Total: {len(rows)} devices")

    def _add(self):    DeviceDialog(self, on_save=self.refresh)
    def _edit(self):
        did = self._sel_id(self._tree)
        if not did: return
        def fn():
            with session_scope() as s:
                return DeviceService(s).get_by_id(did)
        _run(fn, ok_cb=lambda d: DeviceDialog(self, d, on_save=self.refresh) if d else None)

    def _delete(self):
        did = self._sel_id(self._tree)
        if not did: return
        if not messagebox.askyesno("Confirm", "Delete this device?", parent=self): return
        def fn():
            with session_scope() as s:
                DeviceService(s).delete(did)
        _run(fn, ok_cb=lambda _: self.refresh(), err_cb=lambda e: messagebox.showerror("Error", e))


# ── JOBS PAGE ────────────────────────────────────────────────────────────────

class JobsPage(_PageBase):
    """Displays all work orders with status management, logging, and editing."""

    _COL_KEYS = ("id", "cust", "device", "status", "tech", "created", "updated")

    def __init__(self, parent):
        super().__init__(parent); self._build(); self.refresh()

    def _build(self):
        hdr = self._header("🔧  WORK ORDERS")
        bf = ctk.CTkFrame(hdr, fg_color="transparent"); bf.pack(side="right")
        for txt, cmd, col, w in [
            ("➕ New",      self._add,    C["ok"],     90),
            ("🔄 Status",  self._status, "#7b1fa2",  100),
            ("✏️ Edit",    self._edit,   C["accent"],100),
            ("📋 Log",     self._log,    C["bg3"],    80),
            ("🗑️ Delete",  self._delete, C["err"],    80),
            ("⟳",           self.refresh, C["bg3"],   38),
        ]:
            _btn(bf, txt, cmd, col, w).pack(side="left", padx=2)
        wrap, self._tree = _make_tree(self,
            cols=("id","cust","device","status","tech","created","updated"),
            heads=("ID","Customer","Device","Status","Technician","Created","Updated"),
            widths=(45,160,160,140,120,130,130),
            stretch_cols={1,2})
        wrap.pack(fill="both", expand=True, padx=22, pady=(0,4))
        self._sl = self._status_bar()

    def refresh(self):
        def fn():
            with session_scope() as s:
                rows = JobService(s).get_all()
                result = []
                for j in rows:
                    cn = j.customer.name if j.customer else "—"
                    dv = f"{j.device.brand} {j.device.model}" if j.device else "—"
                    tag = "ready" if j.status == "Delivered" else                           "cancel"  if j.status == "Cancelled" else ""
                    result.append((j.id, cn, dv, j.status, j.technician or "—",
                                   j.created_at, j.updated_at, tag))
                return result
        _run(fn, ok_cb=self._fill, err_cb=lambda e: messagebox.showerror("Error", e))

    def _fill(self, rows):
        self._tree.delete(*self._tree.get_children())
        for jid, cn, dv, status, tech, created, updated, tag in rows:
            iid = str(jid)
            self._tree.insert("","end", iid=iid, values=(
                jid, cn, dv, status, tech,
                created.strftime("%d.%m.%Y %H:%M") if created else "",
                updated.strftime("%d.%m.%Y %H:%M") if updated else ""))
            if tag: self._tree.item(iid, tags=(tag,))
        self._tree.tag_configure("ready", background="#193519")
        self._tree.tag_configure("done",  background="#222233")
        self._tree.tag_configure("cancel", background="#3a1010")
        self._sl.configure(text=f"Total: {len(rows)} work orders")

    def _sel(self):
        sel = self._tree.selection()
        if not sel: messagebox.showwarning("Warning", "Please select a work order."); return None, None
        vals = self._tree.item(sel[0])["values"]
        status_idx = self._COL_KEYS.index("status")
        return int(sel[0]), vals[status_idx]

    def _add(self):    JobDialog(self, on_save=self.refresh)
    def _edit(self):
        jid, _ = self._sel()
        if not jid: return
        def fn():
            with session_scope() as s:
                return JobService(s).get_by_id(jid)
        _run(fn, ok_cb=lambda j: JobDialog(self, j, self.refresh) if j else None)

    def _status(self):
        jid, cur = self._sel()
        if jid: StatusDialog(self, jid, cur, on_save=self.refresh)

    def _log(self):
        jid, _ = self._sel()
        if jid: LogDialog(self, jid)

    def _delete(self):
        jid, _ = self._sel()
        if not jid: return
        if not messagebox.askyesno("Confirm", "Delete this work order?", parent=self): return
        def fn():
            with session_scope() as s:
                JobService(s).delete(jid)
        _run(fn, ok_cb=lambda _: self.refresh(), err_cb=lambda e: messagebox.showerror("Error", e))


# ── PAYMENTS PAGE ────────────────────────────────────────────────────────────

class PaymentsPage(_PageBase):
    """Displays all payment records and allows adding or editing payments by job ID."""

    _COL_KEYS = ("id", "job", "cust", "labor", "parts", "total", "paid", "remaining", "date")

    def __init__(self, parent):
        super().__init__(parent); self._build(); self.refresh()

    def _build(self):
        hdr = self._header("💰  PAYMENTS")
        bf = ctk.CTkFrame(hdr, fg_color="transparent"); bf.pack(side="right")
        _btn(bf, "➕ Add / Edit Payment", self._open_payment, C["ok"], 180).pack(side="left", padx=3)
        _btn(bf, "⟳", self.refresh, C["bg3"], 38).pack(side="left", padx=2)
        wrap, self._tree = _make_tree(self,
            cols=("id","job","cust","labor","parts","total","paid","remaining","date"),
            heads=("ID","Job","Customer","Labor","Parts","Total","Paid","Remaining","Date"),
            widths=(45,60,155,88,88,88,88,88,130),
            stretch_cols={2})
        wrap.pack(fill="both", expand=True, padx=22, pady=(0,4))
        self._sum = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12), text_color=C["acc_lite"])
        self._sum.pack(pady=(0,6))

    def refresh(self):
        def fn():
            with session_scope() as s:
                ps = PaymentService(s).get_all_with_jobs()
                data = []
                for p in ps:
                    cn = p.job.customer.name if p.job and p.job.customer else "—"
                    tag = "pend" if p.remaining > 0 else "paid"
                    data.append((p.id, p.job_id, cn, p.labor_cost, p.parts_cost,
                                 p.total_cost, p.paid_amount, p.remaining, p.paid_at, tag))
                total_paid    = sum(p.paid_amount for p in ps)
                total_pending = sum(p.remaining   for p in ps)
                return data, total_paid, total_pending
        def fill(res):
            data, tr, tp = res
            self._tree.delete(*self._tree.get_children())
            for pid, jid, cn, lc, pc, tt, pa, rm, paid_at, tag in data:
                iid = str(pid)
                self._tree.insert("","end", iid=iid, values=(
                    pid, jid, cn,
                    f"{lc:.2f}", f"{pc:.2f}", f"{tt:.2f}",
                    f"{pa:.2f}", f"{rm:.2f}",
                    paid_at.strftime("%d.%m.%Y %H:%M") if paid_at else ""))
                self._tree.item(iid, tags=(tag,))
            self._tree.tag_configure("pend", background="#341a0a")
            self._tree.tag_configure("paid", background="#0a2a0a")
            self._sum.configure(text=f"Total Collected: {tr:.2f}   |   Pending: {tp:.2f}")
        _run(fn, ok_cb=fill, err_cb=lambda e: messagebox.showerror("Error", e))

    def _open_payment(self):
        sel = self._tree.selection()
        top = ctk.CTkToplevel(self); top.title("Job ID"); top.geometry("280x180")
        top.configure(fg_color=C["bg"]); top.grab_set()
        _lbl(top, "Work Order ID:").pack(pady=(18,5))
        je = _entry(top); je.pack(padx=28, fill="x")
        if sel:
            job_idx = self._COL_KEYS.index("job")
            je.insert(0, str(self._tree.item(sel[0])["values"][job_idx]))
        def go():
            try: jid = int(je.get())
            except ValueError:
                messagebox.showwarning("Warning", "Enter a valid ID.", parent=top); return
            def fn():
                with session_scope() as s:
                    job = JobService(s).get_by_id(jid)
                    if not job:
                        raise ValueError(f"Work order not found: ID={jid}")
                    return PaymentService(s).get_by_job(jid)
            def open_dlg(p):
                top.destroy(); PaymentDialog(self, jid, payment=p, on_save=self.refresh)
            _run(fn, ok_cb=open_dlg, err_cb=lambda e: messagebox.showerror("Error", e, parent=top))
        _btn(top, "Continue", go, C["accent"], 100).pack(pady=12)


# ── DASHBOARD PAGE ───────────────────────────────────────────────────────────

class DashboardPage(_PageBase):
    """Overview page showing key metrics via stat cards and a status distribution list."""

    def __init__(self, parent):
        super().__init__(parent); self._build(); self.refresh()

    def _build(self):
        hdr = self._header("📊  DASHBOARD")
        _btn(hdr, "⟳ Refresh", self.refresh, C["bg3"], 100).pack(side="right")
        cards_row = ctk.CTkFrame(self, fg_color="transparent")
        cards_row.pack(fill="x", padx=22, pady=(0,12))
        self._cards = {}
        card_defs = [
            ("active_jobs",      "Active Jobs",       C["warn"]),
            ("ready_jobs",       "Ready for Pickup",  C["ok"]),
            ("total_customers",  "Customers",         C["acc_lite"]),
            ("total_devices",    "Devices",           C["acc_lite"]),
            ("total_jobs",       "Total Work Orders", C["txt"]),
            ("monthly_revenue",  "This Month Revenue",C["ok"]),
            ("pending_payments", "Pending Payments",  C["err"]),
        ]
        for i, (key, title, color) in enumerate(card_defs):
            card = StatCard(cards_row, title, "—", color)
            card.grid(row=0, column=i, padx=6, pady=4, sticky="ew")
            cards_row.grid_columnconfigure(i, weight=1)
            self._cards[key] = card
        _lbl(self, "Status Distribution", 13, bold=True, color=C["acc_lite"]).pack(anchor="w", padx=22, pady=(8,4))
        self._dist_frame = ctk.CTkScrollableFrame(self, fg_color=C["bg2"], corner_radius=8, height=180)
        self._dist_frame.pack(fill="x", padx=22, pady=(0,12))

    def refresh(self):
        def fn():
            with session_scope() as s:
                return DashboardService(s).get_stats()
        _run(fn, ok_cb=self._fill, err_cb=lambda e: messagebox.showerror("Error", e))

    def _fill(self, stats: dict):
        for key, card in self._cards.items():
            val = stats.get(key, 0)
            if isinstance(val, float):
                card.set(f"{val:.2f}")
            else:
                card.set(val)
        for w in self._dist_frame.winfo_children():
            w.destroy()
        dist = stats.get("status_distribution", {})
        total = sum(dist.values()) or 1
        for status, count in sorted(dist.items(), key=lambda x: -x[1]):
            row = ctk.CTkFrame(self._dist_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            _lbl(row, status, 11, color=C["txt"]).pack(side="left", padx=8)
            pct = count / total * 100
            bar_outer = ctk.CTkFrame(row, fg_color=C["bg3"], height=14, corner_radius=4)
            bar_outer.pack(side="left", fill="x", expand=True, padx=(0,8))
            bar_outer.update_idletasks()
            bar_w = max(int(bar_outer.winfo_width() * pct / 100), 4)
            ctk.CTkFrame(bar_outer, fg_color=C["accent"], width=bar_w, height=14, corner_radius=4).place(x=0, y=0)
            _lbl(row, f"{count}  ({pct:.0f}%)", 11, color=C["txt2"]).pack(side="left", padx=4)


# ── SIDEBAR ──────────────────────────────────────────────────────────────────

class Sidebar(ctk.CTkFrame):
    """Vertical navigation sidebar with page buttons and app branding."""

    def __init__(self, parent, navigate_fn):
        super().__init__(parent, fg_color=C["sidebar"], width=210, corner_radius=0)
        self._nav = navigate_fn; self._btns: dict = {}; self._build()

    def _build(self):
        logo = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0); logo.pack(fill="x")
        _lbl(logo, "🔧 REPAIRHUB", 17, bold=True, color=C["acc_lite"]).pack(pady=(18,4))
        _lbl(logo, "Service Management System", 10, color=C["txt2"]).pack(pady=(0,16))
        ctk.CTkFrame(self, height=1, fg_color=C["border"]).pack(fill="x")
        items = [
            ("dashboard", "📊   Dashboard"),
            ("customers", "👤   Customers"),
            ("devices",   "💻   Devices"),
            ("jobs",      "🔧   Work Orders"),
            ("payments",  "💰   Payments"),
        ]
        for pid, lbl in items:
            b = ctk.CTkButton(self, text=lbl, anchor="w",
                    command=lambda p=pid: self._nav(p),
                    fg_color="transparent", hover_color=C["bg3"],
                    text_color=C["txt2"], font=ctk.CTkFont(size=13),
                    height=46, corner_radius=0)
            b.pack(fill="x", pady=1); self._btns[pid] = b
        ctk.CTkFrame(self, fg_color="transparent").pack(fill="both", expand=True)
        _lbl(self, "v1.1  |  RepairHub", 10, color=C["txt2"]).pack(pady=12)

    def activate(self, pid):
        for k, b in self._btns.items():
            b.configure(fg_color=C["accent"] if k == pid else "transparent",
                    text_color="white" if k == pid else C["txt2"])


# ── MAIN APPLICATION WINDOW ──────────────────────────────────────────────────

class RepairHubApp(ctk.CTk):
    """Root application window. Manages the sidebar and page container."""

    def __init__(self):
        global _root
        super().__init__(); _root = self
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.title("RepairHub — Service Management System")
        self.geometry("1300x820"); self.minsize(1050, 660)
        self.configure(fg_color=C["bg"]); _style_tree(); self._build()
        self.navigate("dashboard")

    def _build(self):
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(0, weight=1)
        self._sidebar = Sidebar(self, self.navigate)
        self._sidebar.grid(row=0, column=0, sticky="nsew")
        self._content = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_rowconfigure(0, weight=1); self._content.grid_columnconfigure(0, weight=1)
        self._pages: dict = {
            "dashboard": DashboardPage(self._content),
            "customers": CustomersPage(self._content),
            "devices":   DevicesPage(self._content),
            "jobs":      JobsPage(self._content),
            "payments":  PaymentsPage(self._content),
        }
        for page in self._pages.values():
            page.grid(row=0, column=0, sticky="nsew")

    def navigate(self, pid):
        self._pages[pid].tkraise(); self._sidebar.activate(pid)

    def _on_close(self):
        global _root
        _root = None
        self.destroy()


# ── ENTRY POINT ──────────────────────────────────────────────────────────────

def main():
    app = RepairHubApp(); app.mainloop()
    logger.info("RepairHub closed.")
    _executor.shutdown(wait=True)