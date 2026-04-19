import os
import sqlite3


def migrate():
    """
    Adds missing metrics columns to the routing_logs table in the SQLite database.
    This fixes the 'invalid keyword argument' error when logging confidence and entropy.
    """
    # Try to find the database in the project root or current directory
    db_paths = ["../llm_router.db", "llm_router.db"]
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break

    if not db_path:
        print(
            "Error: Database 'llm_router.db' not found. Please ensure the server has been run at least once."
        )
        return

    print(f"Starting migration on: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # List of columns to ensure exist in the routing_logs table
    new_columns = [
        ("agent_id", "TEXT"),
        ("strategy", "TEXT"),
        ("confidence", "REAL"),
        ("entropy", "REAL"),
        ("logprobs_mean", "REAL"),
        ("logprobs_std", "REAL"),
        ("first_token_logprob", "REAL"),
        ("first_token_top_logprobs", "TEXT"),
        ("second_token_logprob", "REAL"),
        ("second_token_top_logprobs", "TEXT"),
    ]

    try:
        # Check existing columns in the table
        cursor.execute("PRAGMA table_info(routing_logs)")
        columns_info = cursor.fetchall()

        if not columns_info:
            print(
                "Error: Table 'routing_logs' does not exist yet. Run the server first to initialize the DB."
            )
            return

        existing_columns = [col[1] for col in columns_info]

        added_count = 0
        for col_name, col_type in new_columns:
            if col_name not in existing_columns:
                print(f"  -> Adding column: {col_name} ({col_type})")
                cursor.execute(
                    f"ALTER TABLE routing_logs ADD COLUMN {col_name} {col_type}"
                )
                added_count += 1
            else:
                print(f"  -> Column {col_name} already exists.")

        conn.commit()
        if added_count > 0:
            print(f"Successfully added {added_count} columns.")
        else:
            print("Database is already up to date.")

    except Exception as e:
        print(f"Migration failed with error: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
