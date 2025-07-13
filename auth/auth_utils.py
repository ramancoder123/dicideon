from utils.hashing import hash_password, verify_password
import pandas as pd
import os

_current_dir = os.path.dirname(os.path.abspath(__file__))
_data_dir = os.path.join(os.path.dirname(_current_dir), "data")
USERS_FILE = os.path.join(_data_dir, "users.csv")


def authenticate_user(email: str, password: str) -> bool:
    """Check user credentials"""
    users = load_users()
    user = users[users['email'] == email]
    if not user.empty:
        return verify_password(password, user.iloc[0]['password'])
    return False

def register_user(email: str, username: str, password: str):
    """Add new user to database"""
    users = load_users()
    if email in users['email'].values:
        raise ValueError("Email already exists")
    
    new_user = pd.DataFrame([[email, username, hash_password(password)]],
                          columns=['email', 'username', 'password'])
    users = pd.concat([users, new_user])
    users.to_csv(USERS_FILE, index=False)

def load_users():
    """Load user database"""
    if not os.path.exists(USERS_FILE):
        return pd.DataFrame(columns=['email', 'username', 'password'])
    return pd.read_csv(USERS_FILE)