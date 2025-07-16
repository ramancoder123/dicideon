import os
import sys
import pandas as pd
import logging

# Add the project root to the Python path to allow importing 'database'
_current_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_current_dir)
sys.path.append(_root_dir)

import database

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s")


def migrate_users():
    """Migrates data from users.csv to the SQLite users table."""
    users_csv_path = os.path.join(_root_dir, "data", "users.csv")
    if not os.path.exists(users_csv_path):
        logging.warning("users.csv not found, skipping user migration.")
        return

    logging.info("Starting user migration...")
    try:
        df = pd.read_csv(users_csv_path)
        with database.get_db_connection() as conn:
            cursor = conn.cursor()
            for index, row in df.iterrows():
                # Check if user already exists to prevent errors on re-run
                cursor.execute("SELECT id FROM users WHERE email = ?", (row['email'],))
                if cursor.fetchone() is None:
                    cursor.execute(
                        "INSERT INTO users (email, username, password) VALUES (?, ?, ?)",
                        (row['email'], row['username'], row['password'])
                    )
                    logging.info(f"Migrated user: {row['email']}")
            conn.commit()
        logging.info("User migration completed successfully.")
    except Exception as e:
        logging.error(f"An error occurred during user migration: {e}")


if __name__ == "__main__":
    logging.info("--- Starting Database Migration ---")
    # Initialize the database and create tables if they don't exist
    database.init_db()
    migrate_users()
    # NOTE: Add a function call here to migrate pending_requests.csv if it contains live data.
    logging.info("--- Database Migration Finished ---")