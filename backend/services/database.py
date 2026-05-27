import sqlite3
import os
import uuid
import datetime
import random
import bcrypt
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL")

def _is_postgres():
    return DATABASE_URL and (DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://"))

class SQLiteConnectionWrapper:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.conn.rollback()
        else:
            self.conn.commit()
        self.conn.close()

    def execute(self, query, params=None):
        self.conn.row_factory = sqlite3.Row
        cur = self.conn.cursor()
        if params is not None:
            cur.execute(query, params)
        else:
            cur.execute(query)
        return cur

class PostgresConnectionWrapper:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.conn.rollback()
        else:
            self.conn.commit()
        self.conn.close()

    def execute(self, query, params=None):
        # Convert parameter placeholders from sqlite (?) to postgres (%s)
        query = query.replace("?", "%s")
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        if params is not None:
            cur.execute(query, params)
        else:
            cur.execute(query)
        return cur

def _get_conn():
    if _is_postgres():
        conn = psycopg2.connect(DATABASE_URL)
        return PostgresConnectionWrapper(conn)
    else:
        db_dir = os.path.join(os.path.dirname(__file__), "..", "db")
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, "frostguard.db")
        conn = sqlite3.connect(db_path)
        return SQLiteConnectionWrapper(conn)

# ---------------------------------------------------------------------------
# Status pipeline: requested → booked → technician_assigned → in_progress → completed
# ---------------------------------------------------------------------------
VALID_STATUSES = ["requested", "booked", "technician_assigned", "in_progress", "completed"]

def init_db():
    if _is_postgres():
        with _get_conn() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS customers (
                mobile TEXT PRIMARY KEY,
                name TEXT,
                address TEXT,
                pincode TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            conn.execute("""CREATE TABLE IF NOT EXISTS appointments (
                ticket_id TEXT PRIMARY KEY,
                mobile TEXT,
                service_type TEXT,
                scheduled_date TEXT,
                technician TEXT,
                status TEXT DEFAULT 'requested',
                arrival_date TEXT,
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            conn.execute("""CREATE TABLE IF NOT EXISTS escalations (
                ticket_id TEXT PRIMARY KEY,
                mobile TEXT,
                agent_name TEXT,
                eta TEXT,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            conn.execute("""CREATE TABLE IF NOT EXISTS admin_users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")

            # Seed default admin if not exists
            existing = conn.execute("SELECT id FROM admin_users WHERE username = ?", ("admin",)).fetchone()
            if not existing:
                hashed = bcrypt.hashpw("frostguard2024".encode(), bcrypt.gensalt()).decode()
                conn.execute("INSERT INTO admin_users (username, password_hash) VALUES (?, ?)", ("admin", hashed))
    else:
        with _get_conn() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS customers (
                mobile TEXT PRIMARY KEY,
                name TEXT,
                address TEXT,
                pincode TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )""")
            conn.execute("""CREATE TABLE IF NOT EXISTS appointments (
                ticket_id TEXT PRIMARY KEY,
                mobile TEXT,
                service_type TEXT,
                scheduled_date TEXT,
                technician TEXT,
                status TEXT DEFAULT 'requested',
                arrival_date TEXT,
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )""")
            conn.execute("""CREATE TABLE IF NOT EXISTS escalations (
                ticket_id TEXT PRIMARY KEY,
                mobile TEXT,
                agent_name TEXT,
                eta TEXT,
                reason TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )""")
            conn.execute("""CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )""")

            # Seed default admin if not exists
            existing = conn.execute("SELECT id FROM admin_users WHERE username = ?", ("admin",)).fetchone()
            if not existing:
                hashed = bcrypt.hashpw("frostguard2024".encode(), bcrypt.gensalt()).decode()
                conn.execute("INSERT INTO admin_users (username, password_hash) VALUES (?, ?)", ("admin", hashed))

            # Migrate: add missing columns to existing SQLite tables
            _migrate_columns(conn)


def _migrate_columns(conn):
    """Add columns that may be missing from older SQLite schema versions."""
    existing_cols = {r[1] for r in conn.execute("PRAGMA table_info(appointments)").fetchall()}
    migrations = {
        "arrival_date": "ALTER TABLE appointments ADD COLUMN arrival_date TEXT",
        "notes": "ALTER TABLE appointments ADD COLUMN notes TEXT DEFAULT ''",
        "created_at": "ALTER TABLE appointments ADD COLUMN created_at TEXT DEFAULT (datetime('now'))",
        "updated_at": "ALTER TABLE appointments ADD COLUMN updated_at TEXT DEFAULT (datetime('now'))",
    }
    for col, sql in migrations.items():
        if col not in existing_cols:
            try:
                conn.execute(sql)
            except Exception:
                pass

    cust_cols = {r[1] for r in conn.execute("PRAGMA table_info(customers)").fetchall()}
    if "created_at" not in cust_cols:
        try:
            conn.execute("ALTER TABLE customers ADD COLUMN created_at TEXT DEFAULT (datetime('now'))")
        except Exception:
            pass

    esc_cols = {r[1] for r in conn.execute("PRAGMA table_info(escalations)").fetchall()}
    if "created_at" not in esc_cols:
        try:
            conn.execute("ALTER TABLE escalations ADD COLUMN created_at TEXT DEFAULT (datetime('now'))")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Admin Auth
# ---------------------------------------------------------------------------
def verify_admin(username: str, password: str) -> dict:
    with _get_conn() as conn:
        row = conn.execute("SELECT id, username, password_hash FROM admin_users WHERE username = ?", (username,)).fetchone()
        if not row:
            return None
        if bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
            return {"id": row["id"], "username": row["username"]}
        return None


# ---------------------------------------------------------------------------
# Customer operations
# ---------------------------------------------------------------------------
def lookup_customer(mobile: str) -> dict:
    with _get_conn() as conn:
        c = conn.execute("SELECT name, address, pincode FROM customers WHERE mobile = ?", (mobile,)).fetchone()
        if not c:
            return {"status": "not_found"}
        apps = conn.execute("SELECT ticket_id, service_type, scheduled_date, technician, status FROM appointments WHERE mobile = ?", (mobile,)).fetchall()
        return {
            "status": "found",
            "customer": {"name": c["name"], "address": c["address"], "pincode": c["pincode"]},
            "appointments": [{"ticket_id": a["ticket_id"], "service": a["service_type"], "date": a["scheduled_date"], "tech": a["technician"], "status": a["status"]} for a in apps]
        }

def get_all_customers() -> list:
    with _get_conn() as conn:
        rows = conn.execute("SELECT mobile, name, address, pincode, created_at FROM customers ORDER BY created_at DESC").fetchall()
        result = []
        for r in rows:
            appt_count = conn.execute("SELECT COUNT(*) as cnt FROM appointments WHERE mobile = ?", (r["mobile"],)).fetchone()["cnt"]
            result.append({
                "mobile": r["mobile"],
                "name": r["name"],
                "address": r["address"],
                "pincode": r["pincode"],
                "created_at": str(r["created_at"]),
                "appointment_count": appt_count,
            })
        return result


# ---------------------------------------------------------------------------
# Appointment operations
# ---------------------------------------------------------------------------
def book_appointment(name: str, mobile: str, address: str, pincode: str, service_type: str) -> dict:
    with _get_conn() as conn:
        if _is_postgres():
            conn.execute("""
                INSERT INTO customers (mobile, name, address, pincode) VALUES (?, ?, ?, ?)
                ON CONFLICT (mobile) DO UPDATE SET name = EXCLUDED.name, address = EXCLUDED.address, pincode = EXCLUDED.pincode
            """, (mobile, name, address, pincode))
        else:
            conn.execute("INSERT OR REPLACE INTO customers (mobile, name, address, pincode) VALUES (?, ?, ?, ?)", (mobile, name, address, pincode))
            
        ticket_id = f"TKT-{random.randint(100000, 999999)}"
        date = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:00")
        tech = random.choice(["Rajesh", "Amit", "Vikram", "Suresh"])
        now = datetime.datetime.now().isoformat()
        conn.execute(
            "INSERT INTO appointments (ticket_id, mobile, service_type, scheduled_date, technician, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (ticket_id, mobile, service_type, date, tech, "requested", now, now)
        )
        return {"ticket_id": ticket_id, "technician": tech, "date": date, "status": "requested"}


def get_ticket_status(ticket_id: str) -> dict:
    with _get_conn() as conn:
        a = conn.execute("SELECT service_type, scheduled_date, technician, status, arrival_date, notes FROM appointments WHERE ticket_id = ?", (ticket_id,)).fetchone()
        if a:
            return {
                "type": "appointment",
                "service": a["service_type"],
                "date": a["scheduled_date"],
                "tech": a["technician"],
                "status": a["status"],
                "arrival_date": a["arrival_date"],
                "notes": a["notes"],
            }
        return {"status": "not_found"}


def get_all_appointments(status_filter: str = None) -> list:
    with _get_conn() as conn:
        if status_filter and status_filter in VALID_STATUSES:
            rows = conn.execute(
                "SELECT a.ticket_id, a.mobile, a.service_type, a.scheduled_date, a.technician, a.status, a.arrival_date, a.notes, a.created_at, a.updated_at, c.name as customer_name FROM appointments a LEFT JOIN customers c ON a.mobile = c.mobile WHERE a.status = ? ORDER BY a.created_at DESC",
                (status_filter,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT a.ticket_id, a.mobile, a.service_type, a.scheduled_date, a.technician, a.status, a.arrival_date, a.notes, a.created_at, a.updated_at, c.name as customer_name FROM appointments a LEFT JOIN customers c ON a.mobile = c.mobile ORDER BY a.created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]


def get_appointment_detail(ticket_id: str) -> dict:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT a.ticket_id, a.mobile, a.service_type, a.scheduled_date, a.technician, a.status, a.arrival_date, a.notes, a.created_at, a.updated_at, c.name as customer_name, c.address, c.pincode FROM appointments a LEFT JOIN customers c ON a.mobile = c.mobile WHERE a.ticket_id = ?",
            (ticket_id,)
        ).fetchone()
        if row:
            return dict(row)
        return None


def update_appointment_status(ticket_id: str, new_status: str, technician: str = None, arrival_date: str = None, notes: str = None) -> dict:
    if new_status not in VALID_STATUSES:
        return {"error": f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}"}

    with _get_conn() as conn:
        existing = conn.execute("SELECT ticket_id FROM appointments WHERE ticket_id = ?", (ticket_id,)).fetchone()
        if not existing:
            return {"error": "Appointment not found"}

        now = datetime.datetime.now().isoformat()
        updates = ["status = ?", "updated_at = ?"]
        values = [new_status, now]

        if technician is not None:
            updates.append("technician = ?")
            values.append(technician)
        if arrival_date is not None:
            updates.append("arrival_date = ?")
            values.append(arrival_date)
        if notes is not None:
            updates.append("notes = ?")
            values.append(notes)

        values.append(ticket_id)
        conn.execute(f"UPDATE appointments SET {', '.join(updates)} WHERE ticket_id = ?", values)
        return {"status": "updated", "ticket_id": ticket_id, "new_status": new_status}


# ---------------------------------------------------------------------------
# Escalations
# ---------------------------------------------------------------------------
def escalate_to_human(mobile: str, reason: str) -> dict:
    ticket_id = f"TKT-{random.randint(100000, 999999)}"
    eta = "10 minutes"
    agent = random.choice(["Priya", "Rahul", "Neha"])
    with _get_conn() as conn:
        conn.execute("INSERT INTO escalations (ticket_id, mobile, agent_name, eta, reason) VALUES (?, ?, ?, ?, ?)", (ticket_id, mobile, agent, eta, reason))
    return {"ticket_id": ticket_id, "agent": agent, "eta": eta}


def get_all_escalations() -> list:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT e.ticket_id, e.mobile, e.agent_name, e.eta, e.reason, e.created_at, c.name as customer_name FROM escalations e LEFT JOIN customers c ON e.mobile = c.mobile ORDER BY e.created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Dashboard stats
# ---------------------------------------------------------------------------
def get_dashboard_stats() -> dict:
    with _get_conn() as conn:
        total_customers = conn.execute("SELECT COUNT(*) as cnt FROM customers").fetchone()["cnt"]
        total_appointments = conn.execute("SELECT COUNT(*) as cnt FROM appointments").fetchone()["cnt"]
        active_appointments = conn.execute("SELECT COUNT(*) as cnt FROM appointments WHERE status NOT IN ('completed')").fetchone()["cnt"]
        completed_appointments = conn.execute("SELECT COUNT(*) as cnt FROM appointments WHERE status = 'completed'").fetchone()["cnt"]
        total_escalations = conn.execute("SELECT COUNT(*) as cnt FROM escalations").fetchone()["cnt"]

        # Status breakdown
        status_breakdown = {}
        for s in VALID_STATUSES:
            count = conn.execute("SELECT COUNT(*) as cnt FROM appointments WHERE status = ?", (s,)).fetchone()["cnt"]
            status_breakdown[s] = count

        return {
            "total_customers": total_customers,
            "total_appointments": total_appointments,
            "active_appointments": active_appointments,
            "completed_appointments": completed_appointments,
            "total_escalations": total_escalations,
            "status_breakdown": status_breakdown,
        }


# ---------------------------------------------------------------------------
# DB Viewer (raw table access for admin)
# ---------------------------------------------------------------------------
def get_db_tables() -> list:
    if _is_postgres():
        with _get_conn() as conn:
            cur_tables = conn.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """).fetchall()
            result = []
            for t in cur_tables:
                name = t["table_name"]
                count_res = conn.execute(f"SELECT COUNT(*) as cnt FROM {name}").fetchone()
                count = count_res["cnt"]
                cols = conn.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = %s AND table_schema = 'public'
                """, (name,)).fetchall()
                result.append({
                    "name": name,
                    "row_count": count,
                    "columns": [{"name": c["column_name"], "type": c["data_type"]} for c in cols],
                })
            return result
    else:
        with _get_conn() as conn:
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
            result = []
            for t in tables:
                count = conn.execute(f"SELECT COUNT(*) as cnt FROM {t['name']}").fetchone()["cnt"]
                cols = conn.execute(f"PRAGMA table_info({t['name']})").fetchall()
                result.append({
                    "name": t["name"],
                    "row_count": count,
                    "columns": [{"name": c[1], "type": c[2]} for c in cols],
                })
            return result


def get_table_data(table_name: str, limit: int = 100) -> dict:
    # Whitelist tables to prevent SQL injection
    allowed = {"customers", "appointments", "escalations", "admin_users"}
    if table_name not in allowed:
        return {"error": "Table not found"}

    if _is_postgres():
        with _get_conn() as conn:
            cols = conn.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = %s AND table_schema = 'public'
            """, (table_name,)).fetchall()
            column_names = [c["column_name"] for c in cols]
            
            rows = conn.execute(f"SELECT * FROM {table_name} LIMIT %s", (limit,)).fetchall()

            # Hide password hashes from admin_users
            data = []
            for r in rows:
                row_dict = dict(r)
                if table_name == "admin_users" and "password_hash" in row_dict:
                    row_dict["password_hash"] = "***hidden***"
                data.append(row_dict)

            return {
                "table": table_name,
                "columns": column_names,
                "rows": data,
                "total": len(data),
            }
    else:
        with _get_conn() as conn:
            cols = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
            column_names = [c[1] for c in cols]
            rows = conn.execute(f"SELECT * FROM {table_name} LIMIT ?", (limit,)).fetchall()

            # Hide password hashes from admin_users
            data = []
            for r in rows:
                row_dict = dict(r)
                if table_name == "admin_users" and "password_hash" in row_dict:
                    row_dict["password_hash"] = "***hidden***"
                data.append(row_dict)

            return {
                "table": table_name,
                "columns": column_names,
                "rows": data,
                "total": len(data),
            }


init_db()
