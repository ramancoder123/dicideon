import bcrypt
import getpass
import sys
import os

# Add the project root to the Python path to allow importing 'utils'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.hashing import hash_password

def create_admin_user():
    """Securely prompts for admin details and prints a ready-to-use CSV line."""
    try:
        print("--- Create Dicideon Admin User ---")
        email = input("Enter the admin email (e.g., dicideonaccessmanage@gmail.com): ")
        username = input("Enter the admin username (e.g., admin): ")
        password = getpass.getpass("Enter the password for the admin account: ")

        if not all([email, username, password]):
            print("\nError: All fields are required. Aborting.")
            return

        hashed_password = hash_password(password)
        csv_line = f'{email},{username},{hashed_password}'
        
        print("\n✅ Admin user created successfully!")
        print("Copy the line below and paste it into your data/users.csv file (under the header):\n")
        print(csv_line)

    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    create_admin_user()