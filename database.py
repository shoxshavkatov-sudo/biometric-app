import sqlite3
from datetime import datetime

DB_NAME = "attendance.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Таблица сотрудников
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            monthly_salary REAL NOT NULL,
            daily_salary REAL NOT NULL,
            hourly_rate REAL NOT NULL
        )
    ''')

    # Таблица смен (приход/уход)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            check_in TEXT NOT NULL,
            check_out TEXT,
            hours_worked REAL DEFAULT 0,
            earned_salary REAL DEFAULT 0,
            advances REAL DEFAULT 0,
            is_late INTEGER DEFAULT 0,
            status TEXT NOT NULL,
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        )
    ''')

    conn.commit()
    conn.close()


def add_employee(name: str, monthly_salary: float, work_days: int = 22):
    daily_salary = round(monthly_salary / work_days, 2)
    hourly_rate = round(daily_salary / 9.0, 2)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO employees (name, monthly_salary, daily_salary, hourly_rate) VALUES (?, ?, ?, ?)",
        (name, monthly_salary, daily_salary, hourly_rate)
    )
    conn.commit()
    conn.close()


def get_all_employees():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, monthly_salary, daily_salary, hourly_rate FROM employees")
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": r[0], "name": r[1], "monthly_salary": r[2], "daily_salary": r[3], "hourly_rate": r[4]}
        for r in rows
    ]


def add_advance(employee_id: int, amount: float):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE shifts SET advances = advances + ? WHERE employee_id = ? AND date = ?",
        (amount, employee_id, today)
    )
    conn.commit()
    conn.close()


def get_today_summary():
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT e.name, s.check_in, s.check_out, s.hours_worked, s.earned_salary, s.advances, s.is_late, s.status
        FROM shifts s
        JOIN employees e ON s.employee_id = e.id
        WHERE s.date = ?
        ORDER BY s.id DESC
    ''', (today,))
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "name": r[0], "check_in": r[1], "check_out": r[2] or "--:--",
            "hours": r[3], "earned": r[4], "advances": r[5],
            "net_earned": r[4] - r[5], "is_late": bool(r[6]), "status": r[7]
        }
        for r in rows
    ]


init_db()