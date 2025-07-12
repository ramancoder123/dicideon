import re

def validate_email(email: str) -> bool:
    """Check if email is valid"""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def validate_password(password: str) -> bool:
    """Check password requirements"""
    return len(password) >= 8 and any(c.isdigit() for c in password)