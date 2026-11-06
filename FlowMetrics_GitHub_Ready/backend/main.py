"""
FlowMetrics backend using only Python standard-library modules.
No FastAPI, Pydantic, compiled extensions, or pip packages required.
"""

import json
import os
import secrets
import sqlite3
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("FLOWMETRICS_DB_PATH", os.path.join(HERE, "flowmetrics.db"))
TOKENS = {}
ALLOWED_ORIGINS = {
    origin.strip()
    for origin in os.environ.get(
        "FLOWMETRICS_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
}


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL, role TEXT NOT NULL
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL, description TEXT DEFAULT '',
            status TEXT DEFAULT 'Assigned', priority TEXT DEFAULT 'Medium',
            assignee_id INTEGER NOT NULL, leader_id INTEGER NOT NULL,
            due_date TEXT, employee_update TEXT DEFAULT '',
            review_note TEXT DEFAULT '', created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )""")
        if db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            db.executemany(
                "INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
                [
                    (
                        "Aarav Admin",
                        "admin@flowmetrics.local",
                        "FlowMetrics@123",
                        "Admin",
                    ),
                    (
                        "Maya Team Lead",
                        "lead@flowmetrics.local",
                        "FlowMetrics@123",
                        "Team Leader",
                    ),
                    (
                        "Ravi Employee",
                        "employee@flowmetrics.local",
                        "FlowMetrics@123",
                        "Employee",
                    ),
                ],
            )


def user_public(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "role": row["role"],
    }


def task_public(row, db):
    assignee = db.execute(
        "SELECT name FROM users WHERE id=?", (row["assignee_id"],)
    ).fetchone()
    leader = db.execute(
        "SELECT name FROM users WHERE id=?", (row["leader_id"],)
    ).fetchone()
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "status": row["status"],
        "priority": row["priority"],
        "assignee_id": row["assignee_id"],
        "assignee_name": assignee["name"] if assignee else "Unknown",
        "leader_id": row["leader_id"],
        "leader_name": leader["name"] if leader else "Unknown",
        "due_date": row["due_date"],
        "employee_update": row["employee_update"],
        "review_note": row["review_note"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))

    def send_json(self, status, data):
        raw = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        origin = self.headers.get("Origin", "")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.send_header(
            "Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS"
        )
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self):
        self.send_response(204)
        origin = self.headers.get("Origin", "")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.send_header(
            "Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS"
        )
        self.end_headers()

    def body(self):
        length = int(self.headers.get("Content-Length", "0"))
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            raise ValueError("Invalid JSON request body.")

    def auth_user(self, db):
        header = self.headers.get("Authorization", "")
        token = header[7:] if header.startswith("Bearer ") else ""
        uid = TOKENS.get(token)
        return (
            db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
            if uid
            else None
        )

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/api/health"):
            return self.send_json(
                200,
                {
                    "status": "ok",
                    "app": "FlowMetrics",
                    "message": "FlowMetrics API is running",
                },
            )
        with connect() as db:
            user = self.auth_user(db)
            if not user:
                return self.send_json(401, {"detail": "Please sign in."})
            if path == "/api/me":
                return self.send_json(200, user_public(user))
            if path == "/api/users":
                if user["role"] not in ("Admin", "Team Leader"):
                    return self.send_json(
                        403,
                        {"detail": "Only Admins and Team Leaders can view the team."},
                    )
                rows = db.execute(
                    "SELECT * FROM users WHERE role='Employee' ORDER BY name"
                ).fetchall()
                return self.send_json(200, [user_public(r) for r in rows])
            if path == "/api/tasks":
                if user["role"] == "Employee":
                    rows = db.execute(
                        "SELECT * FROM tasks WHERE assignee_id=? ORDER BY updated_at DESC",
                        (user["id"],),
                    ).fetchall()
                elif user["role"] == "Team Leader":
                    rows = db.execute(
                        "SELECT * FROM tasks WHERE leader_id=? ORDER BY updated_at DESC",
                        (user["id"],),
                    ).fetchall()
                else:
                    rows = db.execute(
                        "SELECT * FROM tasks ORDER BY updated_at DESC"
                    ).fetchall()
                return self.send_json(200, [task_public(r, db) for r in rows])
        return self.send_json(404, {"detail": "Endpoint not found."})

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            payload = self.body()
        except ValueError as e:
            return self.send_json(400, {"detail": str(e)})
        if path == "/api/login":
            with connect() as db:
                email = str(payload.get("email", "")).strip().lower()
                password = str(payload.get("password", ""))
                user = db.execute(
                    "SELECT * FROM users WHERE lower(email)=? AND password=?",
                    (email, password),
                ).fetchone()
                if not user:
                    return self.send_json(401, {"detail": "Invalid email or password."})
                token = secrets.token_urlsafe(32)
                TOKENS[token] = user["id"]
                return self.send_json(200, {"token": token, "user": user_public(user)})
        if path == "/api/logout":
            header = self.headers.get("Authorization", "")
            if header.startswith("Bearer "):
                TOKENS.pop(header[7:], None)
            return self.send_json(200, {"ok": True})
        with connect() as db:
            user = self.auth_user(db)
            if not user:
                return self.send_json(401, {"detail": "Please sign in."})
            if path == "/api/tasks":
                if user["role"] not in ("Admin", "Team Leader"):
                    return self.send_json(
                        403, {"detail": "Employees cannot create tasks."}
                    )
                title = str(payload.get("title", "")).strip()
                assignee_id = payload.get("assignee_id")
                if len(title) < 3:
                    return self.send_json(
                        400,
                        {"detail": "Task title must contain at least 3 characters."},
                    )
                employee = db.execute(
                    "SELECT * FROM users WHERE id=? AND role='Employee'", (assignee_id,)
                ).fetchone()
                if not employee:
                    return self.send_json(400, {"detail": "Choose a valid employee."})
                now = datetime.utcnow().isoformat()
                cur = db.execute(
                    """INSERT INTO tasks(title,description,status,priority,assignee_id,leader_id,due_date,created_at,updated_at)
                    VALUES(?,?,?,?,?,?,?,?,?)""",
                    (
                        title,
                        str(payload.get("description", "")),
                        "Assigned",
                        str(payload.get("priority", "Medium")),
                        employee["id"],
                        user["id"],
                        payload.get("due_date") or None,
                        now,
                        now,
                    ),
                )
                db.commit()
                row = db.execute(
                    "SELECT * FROM tasks WHERE id=?", (cur.lastrowid,)
                ).fetchone()
                return self.send_json(201, task_public(row, db))
        return self.send_json(404, {"detail": "Endpoint not found."})

    def do_PATCH(self):
        path = urlparse(self.path).path
        try:
            payload = self.body()
        except ValueError as e:
            return self.send_json(400, {"detail": str(e)})
        parts = path.strip("/").split("/")
        if len(parts) != 4 or parts[0:2] != ["api", "tasks"]:
            return self.send_json(404, {"detail": "Endpoint not found."})
        try:
            task_id = int(parts[2])
        except ValueError:
            return self.send_json(400, {"detail": "Invalid task ID."})
        action = parts[3]
        with connect() as db:
            user = self.auth_user(db)
            if not user:
                return self.send_json(401, {"detail": "Please sign in."})
            task = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
            if not task:
                return self.send_json(404, {"detail": "Task not found."})
            now = datetime.utcnow().isoformat()
            if action == "update":
                if user["role"] != "Employee" or task["assignee_id"] != user["id"]:
                    return self.send_json(
                        403, {"detail": "You can update only tasks assigned to you."}
                    )
                status = payload.get("status")
                if status not in ("In Progress", "Submitted"):
                    return self.send_json(
                        400, {"detail": "Choose In Progress or Submitted."}
                    )
                db.execute(
                    "UPDATE tasks SET status=?, employee_update=?, updated_at=? WHERE id=?",
                    (status, str(payload.get("employee_update", "")), now, task_id),
                )
            elif action == "review":
                if user["role"] not in ("Admin", "Team Leader") or (
                    user["role"] == "Team Leader" and task["leader_id"] != user["id"]
                ):
                    return self.send_json(
                        403, {"detail": "You cannot review this task."}
                    )
                status = payload.get("status", "Reviewed")
                if status not in ("Reviewed", "Assigned", "In Progress"):
                    return self.send_json(400, {"detail": "Invalid review status."})
                db.execute(
                    "UPDATE tasks SET status=?, review_note=?, updated_at=? WHERE id=?",
                    (status, str(payload.get("review_note", "")), now, task_id),
                )
            else:
                return self.send_json(404, {"detail": "Endpoint not found."})
            db.commit()
            row = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
            return self.send_json(200, task_public(row, db))

    def do_DELETE(self):
        path = urlparse(self.path).path
        parts = path.strip("/").split("/")
        if len(parts) != 3 or parts[:2] != ["api", "tasks"]:
            return self.send_json(404, {"detail": "Endpoint not found."})
        try:
            task_id = int(parts[2])
        except ValueError:
            return self.send_json(400, {"detail": "Invalid task ID."})
        with connect() as db:
            user = self.auth_user(db)
            if not user:
                return self.send_json(401, {"detail": "Please sign in."})
            task = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
            if not task:
                return self.send_json(404, {"detail": "Task not found."})
            if user["role"] not in ("Admin", "Team Leader") or (
                user["role"] == "Team Leader" and task["leader_id"] != user["id"]
            ):
                return self.send_json(403, {"detail": "You cannot delete this task."})
            db.execute("DELETE FROM tasks WHERE id=?", (task_id,))
            db.commit()
            return self.send_json(200, {"ok": True})


if __name__ == "__main__":
    init_db()
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", "10000"))

    print(f"FlowMetrics backend starting at http://{host}:{port}")
    print(f"Health check: http://127.0.0.1:{port}/api/health")

    ThreadingHTTPServer((host, port), Handler).serve_forever()
