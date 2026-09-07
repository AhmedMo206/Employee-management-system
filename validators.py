"""
validators.py
Centralized, strict validation rules for the Employee Management System.
Every function raises a ValidationError with a human-readable message
on failure, or returns the cleaned value on success.
"""

import re
from datetime import datetime

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
PHONE_REGEX = re.compile(r"^\+?[0-9]{8,15}$")
NAME_REGEX = re.compile(r"^[A-Za-z\u00C0-\u017F' -]{2,60}$")

MIN_SALARY = 1000.0
MAX_SALARY = 10_000_000.0
MIN_WORKING_AGE_YEARS = 16  # used against hire_date sanity, not birth date
EARLIEST_HIRE_DATE = datetime(1970, 1, 1)


class ValidationError(Exception):
    """Raised when a single field fails validation."""
    def __init__(self, field, message):
        self.field = field
        self.message = message
        super().__init__(message)


def validate_full_name(value: str) -> str:
    value = (value or "").strip()
    if not value:
        raise ValidationError("full_name", "Full name is required.")
    if not NAME_REGEX.match(value):
        raise ValidationError(
            "full_name",
            "Name must be 2-60 letters (spaces, hyphens, apostrophes allowed) "
            "— no numbers or symbols."
        )
    return " ".join(value.split())  # collapse extra whitespace


def validate_email(value: str) -> str:
    value = (value or "").strip().lower()
    if not value:
        raise ValidationError("email", "Email is required.")
    if len(value) > 254:
        raise ValidationError("email", "Email is too long.")
    if not EMAIL_REGEX.match(value):
        raise ValidationError("email", "Enter a valid email address, e.g. name@example.com")
    return value


def validate_phone(value: str) -> str:
    value = (value or "").strip().replace(" ", "").replace("-", "")
    if not value:
        raise ValidationError("phone", "Phone number is required.")
    if not PHONE_REGEX.match(value):
        raise ValidationError(
            "phone",
            "Phone must be 8-15 digits, optionally starting with '+'."
        )
    return value


def validate_gender(value: str) -> str:
    valid = {"Male", "Female", "Other"}
    if value not in valid:
        raise ValidationError("gender", "Please select a gender.")
    return value


def validate_department(value) -> int:
    if value is None or value == "" or value == "Select department":
        raise ValidationError("department", "Please select a department.")
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError("department", "Invalid department selected.")


def validate_position(value: str) -> str:
    value = (value or "").strip()
    if not value:
        raise ValidationError("position", "Job position/title is required.")
    if len(value) < 2 or len(value) > 60:
        raise ValidationError("position", "Position must be between 2 and 60 characters.")
    return value


def validate_salary(value) -> float:
    raw = str(value).strip().replace(",", "")
    if not raw:
        raise ValidationError("salary", "Salary is required.")
    try:
        salary = float(raw)
    except ValueError:
        raise ValidationError("salary", "Salary must be a valid number (e.g. 5000.00).")

    if salary != salary:  # NaN check
        raise ValidationError("salary", "Salary must be a valid number.")
    if salary <= 0:
        raise ValidationError("salary", "Salary must be greater than zero.")
    if salary < MIN_SALARY:
        raise ValidationError(
            "salary", f"Salary seems too low. Minimum allowed is {MIN_SALARY:,.2f}.")
    if salary > MAX_SALARY:
        raise ValidationError(
            "salary", f"Salary exceeds the maximum allowed ({MAX_SALARY:,.2f}).")
    # Restrict to 2 decimal places
    return round(salary, 2)


def validate_hire_date(value: str) -> str:
    value = (value or "").strip()
    if not value:
        raise ValidationError("hire_date", "Hire date is required.")
    try:
        dt = datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise ValidationError("hire_date", "Date must be in YYYY-MM-DD format, e.g. 2024-01-31.")

    if dt > datetime.now():
        raise ValidationError("hire_date", "Hire date cannot be in the future.")
    if dt < EARLIEST_HIRE_DATE:
        raise ValidationError("hire_date", "Hire date is unrealistically old.")
    return value


def validate_address(value: str) -> str:
    value = (value or "").strip()
    if len(value) > 200:
        raise ValidationError("address", "Address is too long (max 200 characters).")
    return value


def validate_department_name(value: str) -> str:
    value = (value or "").strip()
    if not value:
        raise ValidationError("department_name", "Department name is required.")
    if len(value) < 2 or len(value) > 50:
        raise ValidationError("department_name", "Department name must be 2-50 characters.")
    return value


def validate_login(username: str, password: str):
    username = (username or "").strip()
    if not username:
        raise ValidationError("username", "Username is required.")
    if not password:
        raise ValidationError("password", "Password is required.")
    return username, password


def validate_employee_form(raw: dict) -> dict:
    """
    Validates a full employee form dict and returns a cleaned dict ready
    for database insertion/update. Raises ValidationError on the FIRST
    invalid field encountered (caller may choose to validate one at a time
    for more granular UI feedback instead).
    """
    cleaned = {}
    cleaned["full_name"] = validate_full_name(raw.get("full_name"))
    cleaned["email"] = validate_email(raw.get("email"))
    cleaned["phone"] = validate_phone(raw.get("phone"))
    cleaned["gender"] = validate_gender(raw.get("gender"))
    cleaned["department_id"] = validate_department(raw.get("department_id"))
    cleaned["position"] = validate_position(raw.get("position"))
    cleaned["salary"] = validate_salary(raw.get("salary"))
    cleaned["hire_date"] = validate_hire_date(raw.get("hire_date"))
    cleaned["address"] = validate_address(raw.get("address"))
    return cleaned
