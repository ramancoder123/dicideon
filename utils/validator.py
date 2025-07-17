from email_validator import validate_email as validate_email_lib, EmailNotValidError
import phonenumbers
import os
import sys

# --- Add project root to the Python path ---
_current_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_current_dir)
sys.path.append(_root_dir)

import database  # Import the database module

# --- Email Validation ---
def validate_email(email: str) -> bool:
    """
    Check if email is valid using a robust, industry-standard library.
    This is more reliable than a simple regular expression.
    """
    if not email:
        return False
    try:
        # The library checks for valid email format according to IETF standards.
        # We disable check_deliverability to avoid slow DNS lookups in the UI.
        validate_email_lib(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False

# --- Password Validation ---
def validate_password(password: str) -> bool:
    """Check password requirements"""
    return len(password) >= 8 and any(c.isdigit() for c in password)

# --- Phone Number Validation ---
def validate_phone_number(phone_number: str, country_iso2: str) -> bool:
    """m
    Validates a phone number against a specific country ISO code using the phonenumbers library.
    """
    if not phone_number or not country_iso2:
        return False
    try:
        parsed_number = phonenumbers.parse(phone_number, country_iso2)
        return phonenumbers.is_valid_number(parsed_number)
    except phonenumbers.phonenumberutil.NumberParseException:
        return False

# --- Uniqueness Checks ---
def check_uniqueness(email: str, user_id: str, contact_number: str) -> tuple[list[str], dict[str, str]]:
    """
    Checks if email, user_id, or contact_number are already registered or pending.
    Returns a tuple: (list of error messages, dict of notifications to send {'field': 'original_email'}).
    """
    errors = []
    notifications = {}

    with database.get_db_connection() as conn:
        cursor = conn.cursor()

        # --- Email Uniqueness ---
        cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            errors.append("This email address is already registered.")

        # --- User ID Uniqueness ---
        cursor.execute("SELECT username FROM users WHERE username = ?", (user_id,))
        if cursor.fetchone():
            errors.append("This User ID is already registered.")

        # --- Contact Number Uniqueness ---
        # Note: contact numbers should also be checked in the users table.
        cursor.execute("SELECT contact_number FROM users WHERE contact_number = ?", (contact_number,))
        if cursor.fetchone():
            errors.append("This contact number is already registered.")

    return list(set(errors)), notifications