import pandas as pd
import os
import secrets
from datetime import datetime, timedelta
from auth import auth_utils
from utils.hashing import hash_password

# --- Robust Path Definition ---
_current_dir = os.path.dirname(os.path.abspath(__file__))
_data_dir = os.path.join(os.path.dirname(_current_dir), "data")
PASSWORD_RESETS_FILE = os.path.join(_data_dir, "password_resets.csv")

def _create_resets_file_if_not_exists():
    """Ensures the password resets CSV file exists with the correct headers."""
    if not os.path.exists(PASSWORD_RESETS_FILE):
        df = pd.DataFrame(columns=['email', 'token', 'expires_at', 'used'])
        df.to_csv(PASSWORD_RESETS_FILE, index=False)

def generate_reset_token(email: str) -> str | None:
    """
    Generates a secure password reset token if the user exists.
    Stores the token with an expiration date.
    """
    users = auth_utils.load_users()
    if email not in users['email'].values:
        return None  # User does not exist

    _create_resets_file_if_not_exists()
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=1)

    df = pd.read_csv(PASSWORD_RESETS_FILE)
    new_reset_df = pd.DataFrame([{
        'email': email,
        'token': token,
        'expires_at': expires_at,
        'used': False
    }])
    updated_df = pd.concat([df, new_reset_df], ignore_index=True)
    updated_df.to_csv(PASSWORD_RESETS_FILE, index=False)
    return token

def verify_reset_token(token: str) -> str | None:
    """
    Verifies a password reset token.
    Returns the user's email if the token is valid and not expired, otherwise None.
    """
    if not os.path.exists(PASSWORD_RESETS_FILE):
        return None

    df = pd.read_csv(PASSWORD_RESETS_FILE)
    df['token'] = df['token'].astype(str) # Ensure token is read as string
    record = df[(df['token'] == token) & (df['used'] == False)]

    if record.empty:
        return None

    # Ensure 'expires_at' is a datetime object for comparison
    expires_at = pd.to_datetime(record.iloc[0]['expires_at'])
    if datetime.now() > expires_at:
        return None  # Token expired

    return record.iloc[0]['email']

def reset_password(token: str, new_password: str) -> bool:
    """Resets the user's password and invalidates the token."""
    email = verify_reset_token(token)
    if not email:
        return False

    # Update user's password
    users_df = auth_utils.load_users()
    user_index = users_df.index[users_df['email'] == email].tolist()
    if not user_index:
        return False
    users_df.loc[user_index[0], 'password'] = hash_password(new_password)
    users_df.to_csv(auth_utils.USERS_FILE, index=False)

    # Invalidate the token
    resets_df = pd.read_csv(PASSWORD_RESETS_FILE)
    resets_df['token'] = resets_df['token'].astype(str)
    token_index = resets_df.index[resets_df['token'] == token].tolist()
    if token_index:
        resets_df.loc[token_index[0], 'used'] = True
        resets_df.to_csv(PASSWORD_RESETS_FILE, index=False)

    return True