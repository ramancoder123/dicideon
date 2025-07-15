import pytest
from utils import validator

@pytest.mark.parametrize("password, expected", [
    ("password123", True),      # Valid: meets length and has a digit
    ("short1", False),          # Invalid: too short
    ("justletters", False),     # Invalid: no digits
    ("12345678", True),         # Valid: exactly 8 chars with a digit
    ("longpasswordwithonenumber1", True), # Valid
    ("", False),                # Invalid: empty string
])
def test_validate_password(password, expected):
    """Tests the password validation logic with various inputs."""
    assert validator.validate_password(password) == expected

@pytest.mark.parametrize("email, expected", [
    ("test@example.com", True),
    ("invalid-email", False),
    ("test@.com", False),
    ("", False)
])
def test_validate_email(email, expected):
    """Tests the email validation logic."""
    assert validator.validate_email(email) == expected