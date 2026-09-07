"""
gui.py - Contains all Tkinter interface layouts, styles, and window controllers.
"""

import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

from database import Database
from validators import (
    ValidationError,
    validate_full_name, validate_email, validate_phone, validate_gender,
    validate_department, validate_position, validate_salary,
    validate_hire_date, validate_address, validate_department_name,
    validate_login,
)

# ---------------------------------------------------------------------- #
# Color palette / theme constants
# ---------------------------------------------------------------------- #
COLOR_BG = "#f4f6fa"
COLOR_SIDEBAR = "#1f2a44"
COLOR_SIDEBAR_ACTIVE = "#2e3d63"
COLOR_ACCENT = "#3b82f6"
COLOR_ACCENT_DARK = "#2563eb"
COLOR_SUCCESS = "#16a34a"
COLOR_DANGER = "#dc2626"
COLOR_TEXT = "#1f2937"
COLOR_MUTED = "#6b7280"
COLOR_CARD = "#ffffff"
FONT_FAMILY = "Segoe UI"


def style_setup(root):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure("TFrame", background=COLOR_BG)
    style.configure("Card.TFrame", background=COLOR_CARD, relief="flat")
    style.configure("Sidebar.TFrame", background=COLOR_SIDEBAR)

    style.configure("TLabel", background=COLOR_BG, foreground=COLOR_TEXT,
                     font=(FONT_FAMILY, 10))
    style.configure("Card.TLabel", background=COLOR_CARD, foreground=COLOR_TEXT,
                     font=(FONT_FAMILY, 10))
    style.configure("Muted.TLabel", background=COLOR_CARD, foreground=COLOR_MUTED,
                     font=(FONT_FAMILY, 9))
    style.configure("Header.TLabel", background=COLOR_BG, foreground=COLOR_TEXT,
                     font=(FONT_FAMILY, 18, "bold"))
    style.configure("CardTitle.TLabel", background=COLOR_CARD, foreground=COLOR_MUTED,
                     font=(FONT_FAMILY, 9, "bold"))
    style.configure("CardValue.TLabel", background=COLOR_CARD, foreground=COLOR_TEXT,
                     font=(FONT_FAMILY, 20, "bold"))
    style.configure("Error.TLabel", background=COLOR_CARD, foreground=COLOR_DANGER,
                     font=(FONT_FAMILY, 8))
    style.configure("SidebarTitle.TLabel", background=COLOR_SIDEBAR, foreground="white",
                     font=(FONT_FAMILY, 14, "bold"))
    style.configure("SidebarSub.TLabel", background=COLOR_SIDEBAR, foreground="#9aa5c0",
                     font=(FONT_FAMILY, 8))

    style.configure("Sidebar.TButton", background=COLOR_SIDEBAR, foreground="white",
                     font=(FONT_FAMILY, 10), borderwidth=0, anchor="w", padding=(18, 10))
    style.map("Sidebar.TButton",
              background=[("active", COLOR_SIDEBAR_ACTIVE)],
              foreground=[("active", "white")])

    style.configure("SidebarActive.TButton", background=COLOR_SIDEBAR_ACTIVE, foreground="white",
                     font=(FONT_FAMILY, 10, "bold"), borderwidth=0, anchor="w", padding=(18, 10))

    style.configure("Accent.TButton", background=COLOR_ACCENT, foreground="white",
                     font=(FONT_FAMILY, 10, "bold"), padding=(14, 8), borderwidth=0)
    style.map("Accent.TButton", background=[("active", COLOR_ACCENT_DARK)])

    style.configure("Danger.TButton", background=COLOR_DANGER, foreground="white",
                     font=(FONT_FAMILY, 10, "bold"), padding=(14, 8), borderwidth=0)
    style.map("Danger.TButton", background=[("active", "#b91c1c")])

    style.configure("Secondary.TButton", background="#e5e7eb", foreground=COLOR_TEXT,
                     font=(FONT_FAMILY, 10), padding=(14, 8), borderwidth=0)
    style.map("Secondary.TButton", background=[("active", "#d1d5db")])

    style.configure("Treeview", background="white", fieldbackground="white",
                     foreground=COLOR_TEXT, rowheight=28, font=(FONT_FAMILY, 9))
    style.configure("Treeview.Heading", background="#eef1f6", foreground=COLOR_TEXT,
                     font=(FONT_FAMILY, 9, "bold"), relief="flat")
    style.map("Treeview", background=[("selected", COLOR_ACCENT)],
              foreground=[("selected", "white")])

    style.configure("TEntry", padding=6)
    style.configure("TCombobox", padding=6)
    style.configure("TNotebook", background=COLOR_BG)
    style.configure("TNotebook.Tab", padding=(14, 8), font=(FONT_FAMILY, 10))


# ---------------------------------------------------------------------- #
# Reusable validated form field widget
# ---------------------------------------------------------------------- #
class FormField:
    """A labeled input (Entry or Combobox) with an inline error label."""

    def __init__(self, parent, label, row, kind="entry", values=None,
                 show=None, width=32):
        self.var = tk.StringVar()
        ttk.Label(parent, text=label, style="Card.TLabel").grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=(8, 0))

        if kind == "combobox":
            self.widget = ttk.Combobox(parent, textvariable=self.var, values=values,
                                        state="readonly", width=width - 2)
        elif kind == "text":
            self.widget = tk.Text(parent, height=3, width=width, font=(FONT_FAMILY, 10),
                                   relief="solid", borderwidth=1)
        else:
            self.widget = ttk.Entry(parent, textvariable=self.var, width=width, show=show)

        self.widget.grid(row=row, column=1, sticky="w", pady=(8, 0))

        self.error_label = ttk.Label(
            parent,
            text="",
            style="Error.TLabel",
            wraplength=180,
            justify="left"
        )
        self.error_label.grid(row=row, column=2, sticky="w", padx=(8, 0), pady=(8, 0))

    def get(self):
        if isinstance(self.widget, tk.Text):
            return self.widget.get("1.0", "end").strip()
        return self.var.get()

    def set(self, value):
        if isinstance(self.widget, tk.Text):
            self.widget.delete("1.0", "end")
            self.widget.insert("1.0", value or "")
        else:
            self.var.set(value if value is not None else "")

    def set_error(self, message):
        self.error_label.config(text=message or "")

    def clear_error(self):
        self.error_label.config(text="")


# ---------------------------------------------------------------------- #
# Login Window
# ---------------------------------------------------------------------- #
class LoginWindow(tk.Toplevel):
    def __init__(self, master, db, on_success):
        super().__init__(master)
        self.db = db
        self.on_success = on_success
        self.title("Login - Employee Management System")
        self.geometry("420x480")
        self.resizable(False, False)
        self.configure(bg=COLOR_SIDEBAR)
        self.protocol("WM_DELETE_WINDOW", master.destroy)

        wrapper = tk.Frame(self, bg=COLOR_SIDEBAR)
        wrapper.pack(expand=True)

        tk.Label(wrapper, text="👥", bg=COLOR_SIDEBAR, fg="white",
                 font=(FONT_FAMILY, 40)).pack(pady=(40, 0))
        tk.Label(wrapper, text="Employee Management System", bg=COLOR_SIDEBAR,
                 fg="white", font=(FONT_FAMILY, 15, "bold")).pack(pady=(6, 2))
        tk.Label(wrapper, text="Sign in to continue", bg=COLOR_SIDEBAR,
                 fg="#9aa5c0", font=(FONT_FAMILY, 9)).pack(pady=(0, 24))

        card = tk.Frame(wrapper, bg="white", padx=28, pady=28)
        card.pack()

        tk.Label(card, text="Username", bg="white", fg=COLOR_TEXT,
                 font=(FONT_FAMILY, 9, "bold")).grid(row=0, column=0, sticky="w")
        self.username_var = tk.StringVar(value="admin")
        ttk.Entry(card, textvariable=self.username_var, width=28).grid(
            row=1, column=0, pady=(4, 14))

        tk.Label(card, text="Password", bg="white", fg=COLOR_TEXT,
                 font=(FONT_FAMILY, 9, "bold")).grid(row=2, column=0, sticky="w")
        self.password_var = tk.StringVar()
        pw_entry = ttk.Entry(card, textvariable=self.password_var, width=28, show="•")
        pw_entry.grid(row=3, column=0, pady=(4, 4))
        pw_entry.bind("<Return>", lambda e: self.try_login())

        self.error_label = tk.Label(card, text="", bg="white", fg=COLOR_DANGER,
                                     font=(FONT_FAMILY, 8))
        self.error_label.grid(row=4, column=0, sticky="w", pady=(0, 10))

        ttk.Button(card, text="Log In", style="Accent.TButton",
                   command=self.try_login).grid(row=5, column=0, sticky="ew", pady=(6, 0))

        tk.Label(card, text="Default: admin / admin123", bg="white", fg=COLOR_MUTED,
                 font=(FONT_FAMILY, 8)).grid(row=6, column=0, pady=(14, 0))

        self.grab_set()

    def try_login(self):
        try:
            username, password = validate_login(
                self.username_var.get(), self.password_var.get())
        except ValidationError as e:
            self.error_label.config(text=e.message)
            return

        if self.db.verify_user(username, password):
            self.destroy()
            self.on_success(username)
        else:
            self.error_label.config(text="Invalid username or password.")


# ---------------------------------------------------------------------- #
# Employee Form (Add / Edit) Window
# ---------------------------------------------------------------------- #
class EmployeeFormWindow(tk.Toplevel):
    def __init__(self, master, db, on_saved, employee_row=None):
        super().__init__(master)
        self.db = db
        self.on_saved = on_saved
        self.employee_row = employee_row
        self.is_edit = employee_row is not None

        self.title("Edit Employee" if self.is_edit else "Add New Employee")
        self.geometry("680x620")
        self.resizable(False, False)
        self.configure(bg=COLOR_BG)
        self.grab_set()

        header = ttk.Frame(self, style="TFrame")
        header.pack(fill="x", padx=24, pady=(20, 0))
        ttk.Label(header, text=("Edit Employee" if self.is_edit else "Add New Employee"),
                  style="Header.TLabel").pack(anchor="w")
        ttk.Label(header, text="Fields marked are validated automatically on save.",
                  style="TLabel").pack(anchor="w", pady=(2, 0))

        card = ttk.Frame(self, style="Card.TFrame", padding=20)
        card.pack(fill="both", expand=True, padx=24, pady=16)

        departments = self.db.get_departments()
        self.dept_map = {d["name"]: d["id"] for d in departments}
        dept_names = list(self.dept_map.keys())

        self.f_name = FormField(card, "Full Name *", 0)
        self.f_email = FormField(card, "Email *", 1)
        self.f_phone = FormField(card, "Phone *", 2)
        self.f_gender = FormField(card, "Gender *", 3, kind="combobox",
                                   values=["Male", "Female", "Other"])
        self.f_department = FormField(card, "Department *", 4, kind="combobox",
                                       values=dept_names)
        self.f_position = FormField(card, "Position *", 5)
        self.f_salary = FormField(card, "Salary (USD) *", 6)
        self.f_hire_date = FormField(card, "Hire Date * (YYYY-MM-DD)", 7)
        self.f_address = FormField(card, "Address", 8, kind="text")

        if self.is_edit:
            self._populate(employee_row)
        else:
            self.f_hire_date.set(datetime.now().strftime("%Y-%m-%d"))

        btn_row = ttk.Frame(self, style="TFrame")
        btn_row.pack(fill="x", padx=24, pady=(0, 20))
        ttk.Button(btn_row, text="Cancel", style="Secondary.TButton",
                   command=self.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(btn_row, text="Save Employee", style="Accent.TButton",
                   command=self.save).pack(side="right")

    def _populate(self, row):
        self.f_name.set(row["full_name"])
        self.f_email.set(row["email"])
        self.f_phone.set(row["phone"])
        self.f_gender.set(row["gender"])
        self.f_department.set(row["department_name"])
        self.f_position.set(row["position"])
        self.f_salary.set(str(row["salary"]))
        self.f_hire_date.set(row["hire_date"])
        self.f_address.set(row["address"])

    def save(self):
        for f in (self.f_name, self.f_email, self.f_phone, self.f_gender,
                  self.f_department, self.f_position, self.f_salary,
                  self.f_hire_date, self.f_address):
            f.clear_error()

        errors = {}
        cleaned = {}

        def check(fn, field_widget, key, *args):
            try:
                cleaned[key] = fn(*args)
            except ValidationError as e:
                field_widget.set_error(e.message)
                errors[key] = e.message

        check(validate_full_name, self.f_name, "full_name", self.f_name.get())
        check(validate_email, self.f_email, "email", self.f_email.get())
        check(validate_phone, self.f_phone, "phone", self.f_phone.get())
        check(validate_gender, self.f_gender, "gender", self.f_gender.get())

        dept_name = self.f_department.get()
        dept_id = self.dept_map.get(dept_name)
        check(validate_department, self.f_department, "department_id", dept_id)

        check(validate_position, self.f_position, "position", self.f_position.get())
        check(validate_salary, self.f_salary, "salary", self.f_salary.get())
        check(validate_hire_date, self.f_hire_date, "hire_date", self.f_hire_date.get())
        check(validate_address, self.f_address, "address", self.f_address.get())

        if errors:
            return

        exclude_id = self.employee_row["id"] if self.is_edit else None
        if self.db.email_exists(cleaned["email"], exclude_id=exclude_id):
            self.f_email.set_error("This email is already used by another employee.")
            return

        try:
            if self.is_edit:
                self.db.update_employee(self.employee_row["id"], cleaned)
                messagebox.showinfo("Success", "Employee updated successfully.", parent=self)
            else:
                self.db.add_employee(cleaned)
                messagebox.showinfo("Success", "Employee added successfully.", parent=self)
        except Exception as e:
            messagebox.showerror("Database Error", str(e), parent=self)
            return

        self.on_saved()
        self.destroy()


# ---------------------------------------------------------------------- #
# Department Manager Window
# ---------------------------------------------------------------------- #
class DepartmentWindow(tk.Toplevel):
    def __init__(self, master, db, on_change):
        super().__init__(master)
        self.db = db
        self.on_change = on_change
        self.title("Manage Departments")
        self.geometry("420x460")
        self.configure(bg=COLOR_BG)
        self.grab_set()

        ttk.Label(self, text="Departments", style="Header.TLabel").pack(
            anchor="w", padx=20, pady=(20, 10))

        card = ttk.Frame(self, style="Card.TFrame", padding=14)
        card.pack(fill="both", expand=True, padx=20)

        self.listbox = tk.Listbox(card, font=(FONT_FAMILY, 10), relief="flat",
                                   selectbackground=COLOR_ACCENT, height=12)
        self.listbox.pack(fill="both", expand=True, pady=(0, 10))
        self.refresh_list()

        add_row = ttk.Frame(card, style="Card.TFrame")
        add_row.pack(fill="x")
        self.new_dept_var = tk.StringVar()
        ttk.Entry(add_row, textvariable=self.new_dept_var, width=22).pack(
            side="left", padx=(0, 8))
        ttk.Button(add_row, text="Add", style="Accent.TButton",
                   command=self.add_department).pack(side="left")

        self.error_label = ttk.Label(card, text="", style="Error.TLabel")
        self.error_label.pack(anchor="w", pady=(6, 0))

        ttk.Button(self, text="Delete Selected", style="Danger.TButton",
                   command=self.delete_department).pack(pady=14)

    def refresh_list(self):
        self.listbox.delete(0, "end")
        self.depts = self.db.get_departments()
        for d in self.depts:
            self.listbox.insert("end", d["name"])

    def add_department(self):
        try:
            name = validate_department_name(self.new_dept_var.get())
            self.db.add_department(name)
        except ValidationError as e:
            self.error_label.config(text=e.message)
            return
        except Exception as e:
            self.error_label.config(text="Department already exists or DB error.")
            return
        self.error_label.config(text="")
        self.new_dept_var.set("")
        self.refresh_list()
        self.on_change()

    def delete_department(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        dept = self.depts[sel[0]]
        if not messagebox.askyesno("Confirm", f"Delete department '{dept['name']}'?", parent=self):
            return
        try:
            self.db.delete_department(dept["id"])
        except ValueError as e:
            messagebox.showerror("Cannot Delete", str(e), parent=self)
            return
        self.refresh_list()
        self.on_change()


# ---------------------------------------------------------------------- #
# Main Application Window
# ---------------------------------------------------------------------- #
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Employee Management System")
        self.geometry("1180x700")
        self.minsize(1000, 620)
        self.configure(bg=COLOR_BG)
        style_setup(self)

        self.db = Database()
        self.current_user = None
        self.sort_state = {"col": "id", "dir": "ASC"}

        self.withdraw()
        LoginWindow(self, self.db, self.on_login_success)

    def on_login_success(self, username):
        self.current_user = username
        self.deiconify()
        self.build_layout()
        self.show_dashboard()

    def build_layout(self):
        self.sidebar = ttk.Frame(self, style="Sidebar.TFrame", width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        ttk.Label(self.sidebar, text="👥 EMS", style="SidebarTitle.TLabel").pack(
            anchor="w", padx=20, pady=(24, 0))
        ttk.Label(self.sidebar, text=f"Signed in as {self.current_user}",
                  style="SidebarSub.TLabel").pack(anchor="w", padx=20, pady=(2, 24))

        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "📊  Dashboard", self.show_dashboard),
            ("employees", "🧑‍💼  Employees", self.show_employees),
            ("departments", "🏢  Departments", self.open_department_window),
            ("export", "⬇️  Export CSV", self.export_csv),
        ]
        for key, label, cmd in nav_items:
            btn = ttk.Button(self.sidebar, text=label, style="Sidebar.TButton",
                              command=cmd, cursor="hand2")
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[key] = btn

        ttk.Button(self.sidebar, text="🚪  Log Out", style="Sidebar.TButton",
                   command=self.logout).pack(fill="x", padx=10, pady=(30, 2))

        self.content = ttk.Frame(self, style="TFrame")
        self.content.pack(side="left", fill="both", expand=True)

    def set_active_nav(self, key):
        for k, btn in self.nav_buttons.items():
            btn.configure(style="SidebarActive.TButton" if k == key else "Sidebar.TButton")

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def logout(self):
        self.db.close()
        self.destroy()
        new_app = App()
        new_app.mainloop()

    def show_dashboard(self):
        self.set_active_nav("dashboard")
        self.clear_content()
        stats = self.db.get_stats()

        wrapper = ttk.Frame(self.content, style="TFrame", padding=30)
        wrapper.pack(fill="both", expand=True)

        ttk.Label(wrapper, text="Dashboard", style="Header.TLabel").pack(anchor="w")
        ttk.Label(wrapper, text=f"Overview as of {datetime.now().strftime('%B %d, %Y')}",
                  style="TLabel").pack(anchor="w", pady=(0, 20))

        cards_row = ttk.Frame(wrapper, style="TFrame")
        cards_row.pack(fill="x")

        def make_card(parent, title, value, color):
            card = tk.Frame(parent, bg=COLOR_CARD, padx=20, pady=16,
                             highlightbackground="#e5e7eb", highlightthickness=1)
            card.pack(side="left", expand=True, fill="both", padx=(0, 14))
            tk.Label(card, text=title, bg=COLOR_CARD, fg=COLOR_MUTED,
                     font=(FONT_FAMILY, 9, "bold")).pack(anchor="w")
            tk.Label(card, text=value, bg=COLOR_CARD, fg=color,
                     font=(FONT_FAMILY, 22, "bold")).pack(anchor="w", pady=(6, 0))
            return card

        make_card(cards_row, "TOTAL EMPLOYEES", str(stats["total_employees"]), COLOR_ACCENT)
        make_card(cards_row, "TOTAL MONTHLY PAYROLL",
                  f"${stats['total_salary']:,.2f}", COLOR_SUCCESS)
        make_card(cards_row, "AVERAGE SALARY",
                  f"${stats['avg_salary']:,.2f}", "#f59e0b")
        make_card(cards_row, "DEPARTMENTS", str(len(stats["by_department"])), "#8b5cf6")

        chart_card = tk.Frame(wrapper, bg=COLOR_CARD, padx=20, pady=16,
                               highlightbackground="#e5e7eb", highlightthickness=1)
        chart_card.pack(fill="both", expand=True, pady=(24, 0))
        tk.Label(chart_card, text="Employees by Department", bg=COLOR_CARD,
                 fg=COLOR_TEXT, font=(FONT_FAMILY, 11, "bold")).pack(anchor="w", pady=(0, 10))

        canvas = tk.Canvas(chart_card, bg=COLOR_CARD, highlightthickness=0, height=280)
        canvas.pack(fill="both", expand=True)

        rows = stats["by_department"]
        max_count = max([r["cnt"] for r in rows], default=0) or 1
        bar_colors = ["#3b82f6", "#22c55e", "#f59e0b", "#a855f7", "#ec4899", "#14b8a6"]

        def draw_chart(event=None):
            canvas.delete("all")
            width = canvas.winfo_width() or 800
            height = canvas.winfo_height() or 280
            if not rows:
                canvas.create_text(width / 2, height / 2, text="No data yet",
                                    fill=COLOR_MUTED, font=(FONT_FAMILY, 11))
                return
            n = len(rows)
            gap = 24
            bar_width = max(30, (width - gap * (n + 1)) / n)
            base_y = height - 40
            max_bar_height = height - 80

            for i, row in enumerate(rows):
                x0 = gap + i * (bar_width + gap)
                bar_h = (row["cnt"] / max_count) * max_bar_height if max_count else 0
                y0 = base_y - bar_h
                color = bar_colors[i % len(bar_colors)]
                canvas.create_rectangle(x0, y0, x0 + bar_width, base_y,
                                         fill=color, outline="")
                canvas.create_text(x0 + bar_width / 2, y0 - 10, text=str(row["cnt"]),
                                    fill=COLOR_TEXT, font=(FONT_FAMILY, 9, "bold"))
                label = row["name"] if len(row["name"]) <= 12 else row["name"][:10] + "…"
                canvas.create_text(x0 + bar_width / 2, base_y + 16, text=label,
                                    fill=COLOR_MUTED, font=(FONT_FAMILY, 8))

        canvas.bind("<Configure>", draw_chart)

    def show_employees(self):
        self.set_active_nav("employees")
        self.clear_content()

        wrapper = ttk.Frame(self.content, style="TFrame", padding=30)
        wrapper.pack(fill="both", expand=True)

        top_row = ttk.Frame(wrapper, style="TFrame")
        top_row.pack(fill="x")
        ttk.Label(top_row, text="Employees", style="Header.TLabel").pack(side="left")
        ttk.Button(top_row, text="+ Add Employee", style="Accent.TButton",
                   command=self.open_add_employee).pack(side="right")

        filter_row = ttk.Frame(wrapper, style="TFrame")
        filter_row.pack(fill="x", pady=16)

        ttk.Label(filter_row, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_row, textvariable=self.search_var, width=30)
        search_entry.pack(side="left", padx=(8, 20))
        search_entry.bind("<KeyRelease>", lambda e: self.refresh_employee_table())

        ttk.Label(filter_row, text="Department:").pack(side="left")
        dept_names = ["All"] + [d["name"] for d in self.db.get_departments()]
        self.dept_filter_map = {d["name"]: d["id"] for d in self.db.get_departments()}
        self.dept_filter_var = tk.StringVar(value="All")
        dept_combo = ttk.Combobox(filter_row, textvariable=self.dept_filter_var,
                                   values=dept_names, state="readonly", width=22)
        dept_combo.pack(side="left", padx=(8, 0))
        dept_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_employee_table())

        table_card = ttk.Frame(wrapper, style="Card.TFrame", padding=4)
        table_card.pack(fill="both", expand=True)

        columns = ("id", "full_name", "email", "phone", "department_name",
                   "position", "salary", "hire_date")
        headers = {
            "id": "ID", "full_name": "Full Name", "email": "Email", "phone": "Phone",
            "department_name": "Department", "position": "Position",
            "salary": "Salary", "hire_date": "Hire Date"
        }
        self.tree = ttk.Treeview(table_card, columns=columns, show="headings", height=16)
        for col in columns:
            self.tree.heading(col, text=headers[col],
                               command=lambda c=col: self.sort_by(c))
            width = 60 if col == "id" else 130
            self.tree.column(col, width=width, anchor="w")
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind("<Double-1>", lambda e: self.open_edit_employee())

        action_row = ttk.Frame(wrapper, style="TFrame")
        action_row.pack(fill="x", pady=(12, 0))
        ttk.Button(action_row, text="Edit Selected", style="Secondary.TButton",
                   command=self.open_edit_employee).pack(side="left")
        ttk.Button(action_row, text="Delete Selected", style="Danger.TButton",
                   command=self.delete_selected_employee).pack(side="left", padx=(10, 0))

        self.refresh_employee_table()

    def sort_by(self, col):
        if self.sort_state["col"] == col:
            self.sort_state["dir"] = "DESC" if self.sort_state["dir"] == "ASC" else "ASC"
        else:
            self.sort_state = {"col": col, "dir": "ASC"}
        self.refresh_employee_table()

    def refresh_employee_table(self):
        if not hasattr(self, "tree"):
            return
        for row in self.tree.get_children():
            self.tree.delete(row)

        search = self.search_var.get().strip()
        dept_name = self.dept_filter_var.get()
        dept_id = self.dept_filter_map.get(dept_name) if dept_name != "All" else None

        rows = self.db.get_all_employees(
            search_term=search or None,
            department_id=dept_id,
            sort_by=self.sort_state["col"],
            sort_dir=self.sort_state["dir"]
        )
        self._employee_rows_cache = {r["id"]: r for r in rows}
        for r in rows:
            self.tree.insert("", "end", iid=str(r["id"]), values=(
                r["id"], r["full_name"], r["email"], r["phone"],
                r["department_name"], r["position"], f"${r['salary']:,.2f}",
                r["hire_date"]
            ))

    def get_selected_employee(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Please select an employee first.")
            return None
        emp_id = int(sel[0])
        return self.db.get_employee(emp_id)

    def open_add_employee(self):
        EmployeeFormWindow(self, self.db, on_saved=self.refresh_all)

    def open_edit_employee(self):
        row = self.get_selected_employee()
        if row is None:
            return
        EmployeeFormWindow(self, self.db, on_saved=self.refresh_all, employee_row=row)

    def delete_selected_employee(self):
        row = self.get_selected_employee()
        if row is None:
            return
        if messagebox.askyesno("Confirm Delete",
                                f"Delete employee '{row['full_name']}'? This cannot be undone."):
            self.db.delete_employee(row["id"])
            self.refresh_all()

    def refresh_all(self):
        self.refresh_employee_table()

    def open_department_window(self):
        DepartmentWindow(self, self.db, on_change=self.refresh_employee_table)

    def export_csv(self):
        rows = self.db.get_all_employees()
        if not rows:
            messagebox.showinfo("No Data", "There are no employees to export.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="employees_export.csv"
        )
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Full Name", "Email", "Phone", "Gender",
                              "Department", "Position", "Salary", "Hire Date", "Address"])
            for r in rows:
                writer.writerow([r["id"], r["full_name"], r["email"], r["phone"],
                                  r["gender"], r["department_name"], r["position"],
                                  r["salary"], r["hire_date"], r["address"]])
        messagebox.showinfo("Exported", f"Employees exported to:\n{path}")