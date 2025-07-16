import sqlite3

def add_user_columns(db_path="dicideon.db"):
    """
    Adds necessary columns to the user table in the dicideon.db.
    """
    new_columns = {
        "contact_number": "TEXT",
        "phone_code": "TEXT",
        "country": "TEXT",
        "state": "TEXT",
        "city": "TEXT",
        "organization_name": "TEXT",
    }

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Get existing columns
        cursor.execute("PRAGMA table_info(user)")
        existing_columns = [row[1] for row in cursor.fetchall()]

        for column, col_type in new_columns.items():
            if column not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE user ADD COLUMN {column} {col_type}")
                    print(f"Column '{column}' added to 'user' table.")
                except sqlite3.Error as e:
                    print(f"Error adding column {column}: {e}")
            else:
                print(f"Column '{column}' already exists in 'user' table.")
        
        conn.commit()
        print("\nDatabase schema check complete.")

if __name__ == "__main__":
    add_user_columns()