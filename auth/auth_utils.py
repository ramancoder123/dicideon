from utils.hashing import hash_password, verify_password
import os
import sqlite3
import sys

_current_dir = os.path.dirname(os.path.abspath(__file__)) # Path to auth directory
_root_dir = os.path.dirname(_current_dir) # Path to main project dir
sys.path.append(_root_dir) # Add main project dir to path
import database


def authenticate_user(email: str, password: str) -> bool:
    """Check user credentials"""
    user = database.find_user_by_email(email)
    if user:
        # The password from database is not an empty series but a string
        return verify_password(password, user['password'])
    return False

def register_user(email: str, username: str, password: str):
    """Add new user to database. For now, no contact number is added during initial registration."""
    # In a real application, you would store unhashed passwords securely.
    hashed_password = hash_password(password)    # Added the following code to make it work with the database:
     # Added the following code to make it work with the database:
    try:
        database.add_user(email, username, hashed_password)
    except sqlite3.IntegrityError as e:
        # Assuming this exception handles duplicate email errors in the database
        raise ValueError("Email already exists") from e

def add_approved_user(email: str, username: str, hashed_password: str, phone_code: str, contact_number: str, country: str, state: str, city: str, organization_name: str, gender: str):
    """Adds a new user with a pre-hashed password to the database."""    
    try:
        # Now accepts and passes contact_number
        database.add_user(email, username, hashed_password, phone_code, contact_number, country, state, city, organization_name, gender)
    except sqlite3.IntegrityError as e:
        # Assuming this exception handles duplicate email errors in the database
        raise ValueError(f"User with email {email} already exists.") from e