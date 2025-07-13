import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from utils import validator

class TestValidators(unittest.TestCase):

    def test_validate_email(self):
        """Test email validation with valid and invalid formats."""
        self.assertTrue(validator.validate_email("test@example.com"))
        self.assertTrue(validator.validate_email("test.name@example.co.uk"))
        self.assertFalse(validator.validate_email("test@example"))
        self.assertFalse(validator.validate_email("test@.com"))
        self.assertFalse(validator.validate_email("test@gmail.con")) # The specific case you mentioned
        self.assertFalse(validator.validate_email("plainaddress"))
        self.assertFalse(validator.validate_email(""))
        self.assertFalse(validator.validate_email(None))

    def test_validate_password(self):
        """Test password validation for length and digit requirements."""
        self.assertTrue(validator.validate_password("password123"))
        self.assertFalse(validator.validate_password("short1"))
        self.assertFalse(validator.validate_password("passwordwithoutdigit"))
        self.assertFalse(validator.validate_password(""))

    def test_validate_phone_number(self):
        """Test phone number validation with a valid and invalid number for a specific region."""
        # Using 'US' as an example region
        self.assertTrue(validator.validate_phone_number("202-555-0181", "US"))
        self.assertTrue(validator.validate_phone_number("6502530000", "US"))
        self.assertFalse(validator.validate_phone_number("12345", "US"))
        self.assertFalse(validator.validate_phone_number("not a number", "US"))
        self.assertFalse(validator.validate_phone_number("202-555-0181", "GB")) # Valid US number, invalid for GB

    @patch('utils.validator.auth_utils.load_users')
    @patch('utils.validator.pd.read_csv')
    @patch('utils.validator.os.path.exists')
    def test_check_uniqueness(self, mock_exists, mock_read_csv, mock_load_users):
        """Test uniqueness checks by mocking the data sources."""
        # --- Setup Mocks ---
        mock_exists.return_value = True

        # Mock users.csv
        mock_users_df = pd.DataFrame({
            'email': ['user1@test.com', 'admin@test.com'],
            'user_id': ['userone', 'adminuser']
        })
        mock_load_users.return_value = mock_users_df

        # Mock pending_requests_validation.csv
        mock_validation_df = pd.DataFrame({
            'email': ['user2@test.com'],
            'user_id': ['usertwo'],
            'contact_number': ['1234567890']
        })
        mock_read_csv.return_value = mock_validation_df

        # --- Test Scenarios ---

        # 1. No duplicates
        errors, notifications = validator.check_uniqueness("new@test.com", "newuser", "9876543210")
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(notifications), 0)

        # 2. Duplicate email from users.csv
        errors, notifications = validator.check_uniqueness("user1@test.com", "newuser", "9876543210")
        self.assertIn("This email address is already registered or pending approval.", errors)
        self.assertIn('Email Address', notifications)
        self.assertEqual(notifications['Email Address'], 'user1@test.com')

        # 3. Duplicate email from validation.csv
        errors, notifications = validator.check_uniqueness("user2@test.com", "newuser", "9876543210")
        self.assertIn("This email address is already registered or pending approval.", errors)
        self.assertIn('Email Address', notifications)

        # 4. Duplicate user_id from users.csv
        errors, notifications = validator.check_uniqueness("new@test.com", "adminuser", "9876543210")
        self.assertIn("This User ID is already registered or pending approval.", errors)
        self.assertIn('User ID', notifications)
        self.assertEqual(notifications['User ID'], 'admin@test.com')

        # 5. Duplicate contact number from validation.csv
        errors, notifications = validator.check_uniqueness("new@test.com", "newuser", "1234567890")
        self.assertIn("This contact number is already registered or pending approval.", errors)
        self.assertIn('Contact Number', notifications)
        self.assertEqual(notifications['Contact Number'], 'user2@test.com')

if __name__ == '__main__':
    unittest.main()