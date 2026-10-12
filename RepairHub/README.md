# 🔧 RepairHub — Service Management System

A modern, desktop-based repair shop management application built with **Python**, **CustomTkinter**, and **SQLAlchemy**. RepairHub helps small repair businesses track customers, devices, work orders, payments, and status history from a single intuitive interface.

---

## ✨ Features

| Module | Capabilities |
|--------|-------------|
| **Customers** | Create, edit, delete, and search customers by name, phone, or email. View full job history per customer. |
| **Devices** | Register devices linked to customers with brand, model, serial, IMEI, and problem descriptions. |
| **Work Orders** | Manage repair jobs with a strict status workflow, technician assignment, and notes. Full audit log for every status change. |
| **Payments** | Track labor & parts costs, total due, paid amount, and remaining balance. Supports partial payments. |
| **Dashboard** | Real-time overview with KPI cards (active jobs, monthly revenue, pending payments) and a status distribution chart. |

### 🎨 UI Highlights
- **Dark-themed** responsive interface powered by `customtkinter`
- **Background threading** — all database operations run asynchronously so the UI never freezes
- **Color-coded** data tables (green for ready, orange for pending, grey for completed)
- **Modal dialogs** for creating and editing records

---

## 🛠️ Tech Stack

- **Python 3.10+**
- **CustomTkinter** — modern tkinter alternative
- **SQLAlchemy 2.0** — ORM and database management
- **SQLite** — lightweight, file-based database (WAL mode enabled)
- **ThreadPoolExecutor** — concurrent background task execution

---

## 📦 Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/repairhub.git
cd repairhub
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate      # Linux / macOS
venv\Scripts\activate         # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the application
```bash
python -m main
```

> **Note:** The project expects a package structure. Ensure your directory layout matches the structure below before running.

---

## 🗂️ Project Structure

```
repairhub/
├── database/
│   ├── __init__.py
│   └── db.py                 # Engine, session, and init_db()
├── models/
│   ├── __init__.py
│   └── models.py             # SQLAlchemy ORM models
├── services/
│   ├── __init__.py
│   └── services.py           # Business logic & validation
├── frontend/
│   ├── __init__.py
│   └── app.py                # CustomTkinter GUI & dialogs
├── utils/
│   ├── __init__.py
│   └── logger.py             # Rotating file + console logger
├── main.py                   # Application entry point
├── requirements.txt
└── repairhub.db              # Auto-generated SQLite database
```

---

Every transition is recorded in the **Status History** log with a timestamp and action source.

---

## 🧩 Architecture Notes

- **Database Layer**: SQLite with WAL journal mode and foreign key constraints enabled on every connection.
- **Services Layer**: All CRUD operations and domain validation live in service classes (`CustomerService`, `JobService`, etc.), keeping the GUI layer thin.
- **Concurrency**: The GUI delegates all database calls to a `ThreadPoolExecutor`. Results are marshaled back to the main thread via `root.after()` to ensure thread-safe UI updates.
- **Logging**: Dual logging to a rotating file (`repairhub.log`) and the console. Thread names are included in every log entry for easy debugging.

---


<p align="center">
  <i>Built for repair shops that need simplicity, speed, and control.</i>
</p>
