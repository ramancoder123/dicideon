import os
import secrets
from datetime import datetime, timedelta
from utils.hashing import hash_password
import sys
import logging
from typing import Optional

# --- Add project root to the Python path ---
_current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(_current_dir))
import database

def generate_reset_token(email: str) -> Optional[str]:
    """
    Generates a secure password reset token if the user exists.
    Invalidates any old tokens and stores the new one in the database.
    """
    user = database.find_user_by_email(email)
    if not user:
        return None
    try:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=1)
        with database.get_db_connection() as conn:
            cursor = conn.cursor()
            # First, invalidate any old, unused tokens for this user
            cursor.execute("UPDATE password_resets SET used = ? WHERE email = ? AND used = ?", (True, email, False))
            cursor.execute(
                """
                INSERT INTO password_resets (email, token, expires_at, used)
                VALUES (?, ?, ?, ?)
                """,
                (email, token, expires_at.strftime("%Y-%m-%d %H:%M:%S"), False)
            )
            conn.commit()
        return token
    except Exception as e:
        logging.error(f"Failed to generate reset token: {e}")
        return None


def verify_reset_token(token: str) -> Optional[str]:
    """
    Verifies a password reset token.
    Returns the user's email if the token is valid and not expired, otherwise None.
    """
    try:
        with database.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT email, expires_at, used FROM password_resets WHERE token = ?",
                (token,)
            )
            result = cursor.fetchone()
            if result:
                email, expires_at_str, used = result
                expires_at = datetime.strptime(expires_at_str, "%Y-%m-%d %H:%M:%S")
                if not used and datetime.now() <= expires_at:
                    return email
        return None  # Token not found, expired, or already used
    except Exception as e:
        logging.error(f"Failed to verify reset token: {e}")
        return None


def reset_password(token: str, new_password: str) -> bool:
    """Resets the user's password and invalidates the token."""
    email = verify_reset_token(token)
    if not email:
        return False

    try:
        hashed_password = hash_password(new_password)
        with database.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password = ? WHERE email = ?", (hashed_password, email))
            cursor.execute("UPDATE password_resets SET used = ? WHERE token = ?", (True, token))
            conn.commit()
        return True
    except Exception as e:
        logging.error(f"Failed to reset password: {e}")
        return False