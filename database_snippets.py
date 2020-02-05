"""A collection of utility scripts used for creating and managing the SQLite database."""
import argparse
import sqlite3


def create_postings_table(connection: sqlite3.Connection):
    """Creates the postings table which stores information about job postings."""
    query = """
    CREATE TABLE IF NOT EXISTS postings(
        id INTEGER PRIMARY KEY,
        reference, title, superior, institution, deadline, created_at TEXT,
        document BLOB,
        UNIQUE(reference, institution)
    );
    """
    with connection:
        connection.execute(query)


def create_index_on_deadline_date(connection: sqlite3.Connection):
    """Creates an index on `postings.deadline` cast to DATE."""
    query = """
    CREATE INDEX IF NOT EXISTS idx_deadline_as_date
    ON postings (DATE(deadline) ASC);
    """
    with connection:
        connection.execute(query)


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(description="Project e13 database utility.")
    PARSER.add_argument(
        "database_path", type=str, help="database path to sqlite3 instance",
    )
    ARGS = PARSER.parse_args()
    CONNECTION = sqlite3.connect(ARGS.database_path)

    create_postings_table(connection=CONNECTION)
    create_index_on_deadline_date(connection=CONNECTION)
