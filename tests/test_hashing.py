import unittest
from utils.hashing import hash_password, verify_password

class TestHashing(unittest.TestCase):

    def test_hash_and_verify(self):
        """Test that a password can be hashed and then successfully verified."""
        password = "mySecurePassword123"
        hashed_password = hash_password(password)

        self.assertNotEqual(password, hashed_password)
        self.assertTrue(verify_password(password, hashed_password))
        self.assertFalse(verify_password("wrongPassword", hashed_password))