"""A collection of utility scripts used for creating and managing the SQLite database."""
import argparse
import sqlite3


def create_postings_table(connection: sqlite3.Connection):
    """Creates the postings table which stores information about job postings."""
    query = """
    CREATE TABLE IF NOT EXISTS postings(
        id INTEGER PRIMARY KEY,
        reference, title, superior, deadline, created_at TEXT,
        document BLOB
    );
    """
    with connection:
        connection.execute(query)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Project e13 database utility.")
    parser.add_argument(
        "database_path", type=str, help="database path to sqlite3 instance",
    )
    args = parser.parse_args()
    connection = sqlite3.connect(args.database_path)

    create_postings_table(connection)
