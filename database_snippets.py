"""A collection of utility scripts used for creating and managing the SQLite database."""
import argparse
import sqlite3


def activate_foreign_key_support(connection: sqlite3.Connection):
    """
    Per default, foreign key support is deactivated. Running this snippet
    ensures that foreign keys work as expected.
    """
    query = "PRAGMA foreign_keys = ON;"
    with connection:
        connection.execute(query)


def create_postings_table(connection: sqlite3.Connection):
    """Creates the postings table which stores database internals per posting."""
    query = """
    CREATE TABLE IF NOT EXISTS postings(
        id INTEGER PRIMARY KEY,
        created_at TEXT
    );
    """
    with connection:
        connection.execute(query)


def create_metadata_table(connection: sqlite3.Connection):
    """Creates the metadata table which stores metadata of job postings."""
    query = """
    CREATE TABLE IF NOT EXISTS metadata(
        id INTEGER PRIMARY KEY,
        postings_id INTEGER,
        reference, title, superior, institution, deadline TEXT,
        FOREIGN KEY(postings_id) REFERENCES postings(id),
        UNIQUE(reference, institution)
    );
    """
    with connection:
        connection.execute(query)


def create_documents_table(connection: sqlite3.Connection):
    """Creates the documents table which stores PDFs of job postings."""
    query = """
    CREATE TABLE IF NOT EXISTS documents(
        id INTEGER PRIMARY KEY,
        postings_id INTEGER,
        document BLOB,
        FOREIGN KEY(postings_id) REFERENCES postings(id)
    );
    """
    with connection:
        connection.execute(query)


def create_index_for__retrieve_document_by_id(connection: sqlite3.Connection):
    """Creates an index for improving query time on `document_by_id` endpoint."""
    query = """
    CREATE INDEX IF NOT EXISTS idx__retrieve_document_by_id
    ON documents (document ASC, postings_id ASC)
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
    create_metadata_table(connection=CONNECTION)
    create_documents_table(connection=CONNECTION)
    create_index_for__retrieve_document_by_id(connection=CONNECTION)
