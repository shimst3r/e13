"""A collection of utility scripts used for creating and managing the SQLite database."""
import argparse
import io
import sqlite3
from typing import List, Tuple

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser


def activate_foreign_key_support(connection: sqlite3.Connection):
    """
    Per default, foreign key support is deactivated. Running this snippet
    ensures that foreign keys work as expected.
    """
    query = "PRAGMA foreign_keys = ON;"
    with connection:
        connection.execute(query)


def create_table_postings(connection: sqlite3.Connection):
    """Creates the postings table which stores database internals per posting."""
    query = """
    CREATE TABLE IF NOT EXISTS postings(
        id INTEGER PRIMARY KEY,
        created_at TEXT
    );
    """
    with connection:
        connection.execute(query)


def create_table_documents(connection: sqlite3.Connection):
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


def create_table_metadata(connection: sqlite3.Connection):
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


def create_index_for__retrieve_document_by_id(connection: sqlite3.Connection):
    """Creates a covering index for improving query time on `document_by_id` endpoint."""
    query = """
    CREATE INDEX IF NOT EXISTS idx__retrieve_document_by_id
    ON documents (document ASC, postings_id ASC);
    """
    with connection:
        connection.execute(query)


def create_index_for_homepage(connection: sqlite3.Connection):
    """Creates an index for improving query time on `homepage` endpoint."""
    query = """
    CREATE INDEX IF NOT EXISTS idx_homepage
    ON metadata (date(deadline), postings_id, title, superior, institution);
    """
    with connection:
        connection.execute(query)


def create_virtual_table_fulltexts(connection: sqlite3.Connection):
    """
    Creates the fulltexts virtual table which stores full texts using FTS5 to
    enable full-text search.
    """
    query = """
    CREATE VIRTUAL TABLE IF NOT EXISTS fulltexts 
    USING fts5(postings_id, text);
    """
    with connection:
        connection.execute(query)


def populate_virtual_table_fulltexts(connection: sqlite3.Connection):
    """
    Populates the fulltexts virtual table based on the documents in the
    documents table.
    """
    with connection:
        full_texts = _read_and_process_raw_pdf(connection=connection)
        _write_processed_pdfs_as_fulltexts(connection=connection, full_texts=full_texts)


def _process_raw_pdf(document: io.BytesIO) -> str:
    """Reads a raw PDF and returns its content."""
    output_string = io.StringIO()
    parser = PDFParser(document)
    doc = PDFDocument(parser)
    rsrcmgr = PDFResourceManager()
    device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    for page in PDFPage.create_pages(doc):
        interpreter.process_page(page)

    return output_string.getvalue()


def _read_and_process_raw_pdf(connection: sqlite3.Connection) -> List[Tuple[int, str]]:
    query = """
    SELECT postings_id, document
    FROM documents
    """

    full_texts = []
    for postings_id, document in connection.execute(query):
        pdf = io.BytesIO(document)
        text = _process_raw_pdf(pdf)
        full_texts.append((postings_id, text))

    return full_texts


def _write_processed_pdfs_as_fulltexts(
    connection: sqlite3.Connection, full_texts: List[Tuple[int, str]]
):
    query = """
    INSERT INTO fulltexts (postings_id, text)
    VALUES (?, ?)
    """

    connection.executemany(query, full_texts)


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(description="Project e13 database utility.")
    PARSER.add_argument(
        "database_path", type=str, help="database path to sqlite3 instance",
    )
    ARGS = PARSER.parse_args()
    CONNECTION = sqlite3.connect(ARGS.database_path)

    create_table_postings(connection=CONNECTION)
    create_table_documents(connection=CONNECTION)
    create_table_metadata(connection=CONNECTION)
    create_index_for__retrieve_document_by_id(connection=CONNECTION)
    create_index_for_homepage(connection=CONNECTION)
    create_virtual_table_fulltexts(connection=CONNECTION)
    populate_virtual_table_fulltexts(connection=CONNECTION)
