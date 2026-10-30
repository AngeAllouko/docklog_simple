"""Everything that talks to the SQLite database. No screen code here."""
import sqlite3
from contextlib import contextmanager
from datetime import date, timedelta

from settings import DB_NAME


@contextmanager
def connect():
    """Open the database; save changes when done and always close it."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def initialize_database():
    today = date.today()
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                vessel TEXT NOT NULL,
                location TEXT NOT NULL,
                status TEXT NOT NULL,
                next_maintenance TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_id INTEGER NOT NULL,
                maintenance_date TEXT NOT NULL,
                description TEXT NOT NULL,
                cost REAL NOT NULL DEFAULT 0,
                outcome TEXT NOT NULL,
                FOREIGN KEY (equipment_id)
                    REFERENCES equipment(id) ON DELETE CASCADE
            )
        """)

        # Demo equipment, only when the table is empty
        if conn.execute("SELECT COUNT(*) FROM equipment").fetchone()[0] == 0:
            def in_days(n):
                return (today + timedelta(days=n)).isoformat()

            conn.executemany("""
                INSERT INTO equipment
                (name, vessel, location, status, next_maintenance)
                VALUES (?, ?, ?, ?, ?)
            """, [
                ("Radar System", "INS Example", "Bridge", "Operational", in_days(15)),
                ("Main Engine", "INS Example", "Engine Room", "Operational", in_days(30)),
                ("Navigation System", "INS Example", "Bridge", "Under Maintenance", in_days(5)),
                ("Emergency Generator", "INS Example", "Engine Room", "Operational", in_days(-3)),
                ("Communication Radio", "INS Example", "Radio Room", "Out of Service", in_days(10)),
            ])


# ---------------------------------------------------------------- equipment

COLUMNS = "id, name, vessel, location, status, next_maintenance"


def fetch_equipment(search="", status="All"):
    with connect() as conn:
        rows = conn.execute(
            f"SELECT {COLUMNS} FROM equipment ORDER BY id DESC").fetchall()

    if status != "All":
        rows = [r for r in rows if r[4] == status]

    search = search.strip().lower()
    if search:
        rows = [r for r in rows
                if search in " ".join(str(v) for v in r).lower()]
    return rows


def get_equipment(equipment_id):
    with connect() as conn:
        return conn.execute(
            f"SELECT {COLUMNS} FROM equipment WHERE id = ?",
            (equipment_id,)).fetchone()


def insert_equipment(name, vessel, location, status, next_maintenance):
    with connect() as conn:
        conn.execute("""
            INSERT INTO equipment
            (name, vessel, location, status, next_maintenance)
            VALUES (?, ?, ?, ?, ?)
        """, (name, vessel, location, status, next_maintenance))


def update_equipment(equipment_id, name, vessel, location, status,
                     next_maintenance):
    with connect() as conn:
        conn.execute("""
            UPDATE equipment
            SET name=?, vessel=?, location=?, status=?, next_maintenance=?
            WHERE id=?
        """, (name, vessel, location, status, next_maintenance, equipment_id))


def delete_equipment(equipment_id):
    """Its maintenance logs are deleted too (ON DELETE CASCADE)."""
    with connect() as conn:
        conn.execute("DELETE FROM equipment WHERE id = ?", (equipment_id,))


# -------------------------------------------------------------- maintenance

def fetch_maintenance():
    with connect() as conn:
        return conn.execute("""
            SELECT m.id, m.equipment_id, e.name, e.vessel,
                   m.maintenance_date, m.description, m.cost, m.outcome
            FROM maintenance_log m
            JOIN equipment e ON e.id = m.equipment_id
            ORDER BY m.maintenance_date DESC, m.id DESC
        """).fetchall()


def add_maintenance(equipment_id, maintenance_date, description, cost,
                    outcome, new_status=None, next_maintenance=None):
    """Save a log. If new_status is given, update the equipment as well
    (both changes are saved together or not at all)."""
    with connect() as conn:
        conn.execute("""
            INSERT INTO maintenance_log
            (equipment_id, maintenance_date, description, cost, outcome)
            VALUES (?, ?, ?, ?, ?)
        """, (equipment_id, maintenance_date, description, cost, outcome))

        if new_status:
            conn.execute(
                "UPDATE equipment SET status = ?, next_maintenance = ? "
                "WHERE id = ?", (new_status, next_maintenance, equipment_id))


def delete_maintenance(log_id):
    with connect() as conn:
        conn.execute("DELETE FROM maintenance_log WHERE id = ?", (log_id,))


# ------------------------------------------------------------------ reports

def report_data(start, end):
    """Returns (jobs, total_cost), spending by vessel, spending by equipment."""
    with connect() as conn:
        by_vessel = conn.execute("""
            SELECT e.vessel, COUNT(m.id), SUM(m.cost)
            FROM maintenance_log m JOIN equipment e ON e.id = m.equipment_id
            WHERE m.maintenance_date BETWEEN ? AND ?
            GROUP BY e.vessel ORDER BY SUM(m.cost) DESC
        """, (start, end)).fetchall()

        by_equipment = conn.execute("""
            SELECT e.name, e.vessel, COUNT(m.id), SUM(m.cost)
            FROM maintenance_log m JOIN equipment e ON e.id = m.equipment_id
            WHERE m.maintenance_date BETWEEN ? AND ?
            GROUP BY e.id ORDER BY SUM(m.cost) DESC
        """, (start, end)).fetchall()

        summary = conn.execute("""
            SELECT COUNT(*), COALESCE(SUM(cost), 0)
            FROM maintenance_log WHERE maintenance_date BETWEEN ? AND ?
        """, (start, end)).fetchone()

    return summary, by_vessel, by_equipment


def monthly_costs(months=6):
    """Total cost for each of the last `months` months: [("Oct", 1500.0), ...]"""
    today = date.today()
    year = today.year
    month = today.month
    wanted = []  # (year, month), newest first
    for _ in range(months):
        wanted.append((year, month))
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    wanted.reverse()

    first_day = f"{wanted[0][0]:04d}-{wanted[0][1]:02d}-01"
    with connect() as conn:
        rows = conn.execute("""
            SELECT substr(maintenance_date, 1, 7), SUM(cost)
            FROM maintenance_log WHERE maintenance_date >= ? GROUP BY 1
        """, (first_day,)).fetchall()
    totals = dict(rows)

    names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
             "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return [(names[m - 1], totals.get(f"{y:04d}-{m:02d}", 0.0))
            for y, m in wanted]
