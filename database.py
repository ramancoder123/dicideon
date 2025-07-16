import sqlite3
import os
import logging
import datetime
from typing import Optional, List, Dict, Any, Tuple

# --- DATABASE SETUP ---
_current_dir = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(_current_dir, "data", "dicideon.db")


def get_db_connection() -> sqlite3.Connection:
    """Establishes and returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    # This allows you to access columns by name
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Initializes the database and creates the necessary tables if they don't exist.
    This is safe to run every time the application starts.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # --- Users Table ---
            # Stores registered and approved users
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL,
                    phone_code TEXT,
                    contact_number TEXT,
                    country TEXT,
                    state TEXT,
                    city TEXT,
                    contact_number TEXT,  -- Added contact number
                    organization_name TEXT,
                    gender TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Add new columns if they don't exist
            cursor.execute("""
                ALTER TABLE users ADD COLUMN phone_code TEXT
            """)
            cursor.execute("""
                ALTER TABLE users ADD COLUMN country TEXT
            """)
            cursor.execute("""
                ALTER TABLE users ADD COLUMN state TEXT
            """)
            cursor.execute("""
                ALTER TABLE users ADD COLUMN city TEXT
            """)

            # --- Requests Table ---
            # Stores pending sign-up requests for admin approval
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_timestamp TIMESTAMP NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('pending_otp', 'pending_approval', 'approved', 'rejected')),
                    email TEXT NOT NULL UNIQUE,
                    user_id TEXT NOT NULL UNIQUE,
                    first_name TEXT NOT NULL,
                    middle_name TEXT,
                    last_name TEXT NOT NULL,
                    country_code TEXT NOT NULL,
                    contact_number TEXT NOT NULL UNIQUE,
                    date_of_birth DATE NOT NULL,
                    gender TEXT NOT NULL,
                    organization_name TEXT NOT NULL,
                    country TEXT NOT NULL,
                    state TEXT NOT NULL,
                    city TEXT NOT NULL,
                    user_password TEXT NOT NULL,
                    otp TEXT,
                    otp_expires_at TIMESTAMP
                )
            """)

            # --- Password Resets Table ---
            # Stores password reset tokens and their status
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS password_resets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    token TEXT NOT NULL UNIQUE,
                    expires_at TIMESTAMP NOT NULL,
                    used BOOLEAN NOT NULL DEFAULT FALSE
                )
            """)
            conn.commit()
            logging.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logging.error(f"Database error during initialization: {e}")
        raise


# --- USER MANAGEMENT FUNCTIONS ---

def find_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Finds a user by their email in the 'users' table."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        return dict(user) if user else None

def add_user(email: str, username: str, hashed_password: str) -> None:
    """Adds a new, approved user to the 'users' table."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (email, username, password, phone_code, contact_number, country, state, city, organization_name, gender) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (email, username, hashed_password, phone_code, contact_number, country, state, city, organization_name, gender)
        )
        conn.commit()


# --- REQUEST MANAGEMENT FUNCTIONS ---

def get_request_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Finds a sign-up request by email in the 'requests' table."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM requests WHERE email = ?", (email,))
        request = cursor.fetchone()
        return dict(request) if request else None

def get_all_pending_requests() -> List[Dict[str, Any]]:
    """Retrieves all requests with 'pending_approval' status."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM requests WHERE status = 'pending_approval' ORDER BY request_timestamp DESC")
        requests = cursor.fetchall()
        return [dict(row) for row in requests]

def update_request_status(email: str, new_status: str) -> None:
    """Updates the status of a specific request."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE requests SET status = ? WHERE email = ?", (new_status, email))
        conn.commit()

def create_pending_request(request_data: Dict[str, Any]) -> None:
    """
    Creates or replaces a sign-up request in the 'requests' table.
    This ensures that if a user tries to sign up again, their old request is replaced.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Use INSERT OR REPLACE to handle cases where a user re-submits the form.
        # The UNIQUE constraint on the email column is key here.
        cursor.execute("""
            INSERT OR REPLACE INTO requests (
                request_timestamp, status, email, user_id, first_name, middle_name,
                last_name, country_code, contact_number, date_of_birth, gender,
                organization_name, country, state, city, user_password, otp, otp_expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request_data.get('request_timestamp'),
            request_data.get('status'),
            request_data.get('email'),
            request_data.get('user_id'),
            request_data.get('first_name'),
            request_data.get('middle_name'),
            request_data.get('last_name'),
            request_data.get('country_code'),
            request_data.get('contact_number'),
            request_data.get('date_of_birth'),
            request_data.get('gender'),
            request_data.get('organization_name'),
            request_data.get('country'),
            request_data.get('state'),
            request_data.get('city'),
            request_data.get('user_password'),
            request_data.get('otp'),
            request_data.get('otp_expires_at')
        ))
        conn.commit()

def update_request_otp(email: str, otp: str, expires_at: datetime) -> None:
    """Updates the OTP and its expiration time for a specific request."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE requests SET otp = ?, otp_expires_at = ? WHERE email = ?",
            (otp, expires_at.strftime("%Y-%m-%d %H:%M:%S"), email)
        )
        conn.commit()

# --- UNIQUENESS AND LOOKUP FUNCTIONS ---

def is_email_unique(email: str) -> bool:
    """Checks if an email exists in either the users or requests table."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            return False
        cursor.execute("SELECT id FROM requests WHERE email = ?", (email,))
        if cursor.fetchone():
            return False
    return True

def is_user_id_unique(user_id: str) -> bool:
    """Checks if a user_id/username exists in either the users or requests table."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Check 'username' column in 'users' table
        cursor.execute("SELECT id FROM users WHERE username = ?", (user_id,))
        if cursor.fetchone():
            return False
        # Check 'user_id' column in 'requests' table
        cursor.execute("SELECT id FROM requests WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            return False
    return True

def is_contact_number_unique(contact_number: str) -> bool:
    """Checks if a contact number exists in the requests table."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM requests WHERE contact_number = ?", (contact_number,))
        return cursor.fetchone() is None

def get_request_by_user_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Finds a sign-up request by its user_id."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM requests WHERE user_id = ?", (user_id,))
        request = cursor.fetchone()
        return dict(request) if request else None

def get_request_by_contact_number(contact_number: str) -> Optional[Dict[str, Any]]:
    """Finds a sign-up request by its contact number."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM requests WHERE contact_number = ?", (contact_number,))
        request = cursor.fetchone()
        return dict(request) if request else None