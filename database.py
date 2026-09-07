"""
database.py
Handles all SQLite database interactions for the Employee Management System.
"""

import sqlite3
import hashlib
import os
from datetime import datetime

DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ems.db")


class Database:
    def __init__(self, db_path=DB_NAME):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._create_tables()
        self._seed_default_data()

    # ------------------------------------------------------------------ #
    # Schema
    # ------------------------------------------------------------------ #
    def _create_tables(self):
        self.cursor.executescript("""
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            gender TEXT NOT NULL,
            department_id INTEGER NOT NULL,
            position TEXT NOT NULL,
            salary REAL NOT NULL,
            hire_date TEXT NOT NULL,
            address TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (department_id) REFERENCES departments (id)
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'admin'
        );
        """)
        self.conn.commit()

    def _seed_default_data(self):
        # Default admin user: admin / admin123
        self.cursor.execute("SELECT COUNT(*) FROM users")
        if self.cursor.fetchone()[0] == 0:
            self.create_user("admin", "admin123", "admin")

        # Default departments
        defaults = ["Human Resources", "Engineering", "Sales",
                    "Marketing", "Finance", "Operations"]
        for d in defaults:
            try:
                self.cursor.execute(
                    "INSERT INTO departments (name) VALUES (?)", (d,))
            except sqlite3.IntegrityError:
                pass
        self.conn.commit()

    # ------------------------------------------------------------------ #
    # Users / Auth
    # ------------------------------------------------------------------ #
    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def create_user(self, username, password, role="admin"):
        self.cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, self._hash_password(password), role)
        )
        self.conn.commit()

    def verify_user(self, username, password) -> bool:
        self.cursor.execute(
            "SELECT password_hash FROM users WHERE username = ?", (username,))
        row = self.cursor.fetchone()
        if not row:
            return False
        return row["password_hash"] == self._hash_password(password)

    # ------------------------------------------------------------------ #
    # Departments
    # ------------------------------------------------------------------ #
    def get_departments(self):
        self.cursor.execute("SELECT * FROM departments ORDER BY name")
        return self.cursor.fetchall()

    def add_department(self, name):
        self.cursor.execute("INSERT INTO departments (name) VALUES (?)", (name,))
        self.conn.commit()

    def delete_department(self, dept_id):
        self.cursor.execute("SELECT COUNT(*) FROM employees WHERE department_id=?", (dept_id,))
        if self.cursor.fetchone()[0] > 0:
            raise ValueError("Cannot delete a department that still has employees assigned.")
        self.cursor.execute("DELETE FROM departments WHERE id=?", (dept_id,))
        self.conn.commit()

    # ------------------------------------------------------------------ #
    # Employees (CRUD)
    # ------------------------------------------------------------------ #
    def add_employee(self, data: dict):
        self.cursor.execute("""
            INSERT INTO employees
            (full_name, email, phone, gender, department_id, position, salary, hire_date, address)
            VALUES (:full_name, :email, :phone, :gender, :department_id, :position,
                    :salary, :hire_date, :address)
        """, data)
        self.conn.commit()
        return self.cursor.lastrowid

    def update_employee(self, emp_id, data: dict):
        data["id"] = emp_id
        self.cursor.execute("""
            UPDATE employees SET
                full_name=:full_name, email=:email, phone=:phone, gender=:gender,
                department_id=:department_id, position=:position, salary=:salary,
                hire_date=:hire_date, address=:address
            WHERE id=:id
        """, data)
        self.conn.commit()

    def delete_employee(self, emp_id):
        self.cursor.execute("DELETE FROM employees WHERE id=?", (emp_id,))
        self.conn.commit()

    def get_employee(self, emp_id):
        self.cursor.execute("""
            SELECT e.*, d.name AS department_name FROM employees e
            JOIN departments d ON e.department_id = d.id
            WHERE e.id = ?
        """, (emp_id,))
        return self.cursor.fetchone()

    def email_exists(self, email, exclude_id=None):
        if exclude_id:
            self.cursor.execute(
                "SELECT COUNT(*) FROM employees WHERE email=? AND id != ?",
                (email, exclude_id))
        else:
            self.cursor.execute(
                "SELECT COUNT(*) FROM employees WHERE email=?", (email,))
        return self.cursor.fetchone()[0] > 0

    def get_all_employees(self, search_term=None, department_id=None,
                           sort_by="id", sort_dir="ASC"):
        query = """
            SELECT e.*, d.name AS department_name FROM employees e
            JOIN departments d ON e.department_id = d.id
            WHERE 1=1
        """
        params = []
        if search_term:
            query += """ AND (e.full_name LIKE ? OR e.email LIKE ?
                         OR e.position LIKE ? OR d.name LIKE ?)"""
            like = f"%{search_term}%"
            params.extend([like, like, like, like])
        if department_id and department_id != "All":
            query += " AND e.department_id = ?"
            params.append(department_id)

        allowed_cols = {"id", "full_name", "email", "phone", "department_name",
                         "position", "salary", "hire_date"}
        if sort_by not in allowed_cols:
            sort_by = "id"
        sort_dir = "DESC" if str(sort_dir).upper() == "DESC" else "ASC"
        query += f" ORDER BY {sort_by} {sort_dir}"

        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    # ------------------------------------------------------------------ #
    # Stats
    # ------------------------------------------------------------------ #
    def get_stats(self):
        stats = {}
        self.cursor.execute("SELECT COUNT(*) FROM employees")
        stats["total_employees"] = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT COALESCE(SUM(salary),0) FROM employees")
        stats["total_salary"] = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT COALESCE(AVG(salary),0) FROM employees")
        stats["avg_salary"] = self.cursor.fetchone()[0]

        self.cursor.execute("""
            SELECT d.name, COUNT(e.id) as cnt
            FROM departments d LEFT JOIN employees e ON d.id = e.department_id
            GROUP BY d.id ORDER BY cnt DESC
        """)
        stats["by_department"] = self.cursor.fetchall()
        return stats

    def close(self):
        self.conn.close()
