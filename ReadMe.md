# Employee Management System (Python + Tkinter + SQLite)

  

A complete desktop Employee Management System with a modern GUI, a real SQLite database, and strict validation on every field.

  

## Features

  

* **Login screen:** default `admin` / `admin123` (stored as a hashed password).

* **Dashboard with live stats:** total employees, total payroll, average salary, and a bar chart of employees per department.

* **Employee CRUD:** add, edit, delete, search, filter by department, and sort by any column (click a column header).

* **Department manager:** add/delete departments (blocks deleting a department that still has employees).

* **CSV export** of the full employee list.

* **Strict validation on every input:**

  * **Full name:** letters only, 2–60 characters.

  * **Email:** valid format and must be unique across employees.

  * **Phone:** 8–15 digits, optional leading `+`.

  * **Gender / Department:** must be selected from the list.

  * **Position:** 2–60 characters.

  * **Salary:** must be numeric, greater than 0, within a sane min/max range (1,000 – 10,000,000), rounded to 2 decimals — rejects text, negative numbers, and unrealistic values.

  * **Hire date:** must be `YYYY-MM-DD`, cannot be in the future or before 1970.

  * **Address:** optional, max 200 characters.

* **Error handling:** Every error is shown inline, next to the exact field that failed.

  

## Requirements

  

* **Python 3.8+**

* No third-party packages required — uses only the standard library (`tkinter`, `sqlite3`, `hashlib`, `csv`).

  

## Run It

```bash

python main.py
  
```

## Project structure


```
Employee-management-system/

├── main.py        # Entry point to launch the application
├── GUI.py         # Tkinter interface, layouts, and window controllers
├── database.py    # SQLite schema + all CRUD operations
├── validators.py  # All field validation rules and error messages
├── .gitignore     # Git ignore rules for venv, cache, and DB files
└── ems.db         # Created automatically on first run

  
```


  

