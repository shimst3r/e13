# -*- coding: utf-8 -*-
import logging
import pathlib
import re
import sqlite3
import typing
from datetime import date

import scrapy

BASE_URL = "https://www.uni-bielefeld.de/Universitaet/Aktuelles/Stellenausschreibungen"
LOGGER = logging.getLogger(__name__)
DATE_FMT = "%Y-%m-%d"


def clean_posting_text(text: str) -> typing.Optional[typing.List[str]]:
    """Clean and process the metadata that is scraped for each postings entry."""
    try:
        reference, title, superior, deadline = text.split("\n\n")
        if match := re.search(r"wiss\d+", reference):
            reference = match.group()
        if match := re.search(r"\d{2}.\d{2}.\d{4}", deadline):
            day, month, year = match.group().split(".")
            deadline = f"{year}-{month}-{day}"
    except ValueError as value_error:
        LOGGER.error(value_error)
        return None
    else:
        return [reference, title, superior, deadline]


class BielefeldUniversitySpider(scrapy.Spider):
    """A spider for scraping academic job postings from Bielefeld University."""

    name = "bielefeld_university"
    institution = "Bielefeld University"
    start_urls = [f"{BASE_URL}/auswiss_2013.html/"]

    def parse(self, response):
        # Line breaks make accessing content via CSS selectors more difficult,
        # hence they're removed.
        response = response.replace(body=response.body.replace(b"<br>", b""))
        for posting in response.css("a.intern"):
            postings_id = self._create_posting()
            metadata = posting.css("::text").get()
            self._create_metadata(postings_id=postings_id, metadata=metadata)

            try:
                pdf_url = posting.attrib["href"]
            except KeyError as key_error:
                LOGGER.error(key_error)
            else:
                yield scrapy.Request(
                    f"{BASE_URL}/{pdf_url}",
                    callback=self.parse_pdf,
                    cb_kwargs={"metadata": {"postings_id": postings_id}},
                )

    def parse_pdf(self, response, metadata):
        """Retrieve a job postings PDF and insert it into the database."""
        postings_id = metadata["postings_id"]
        document = response.body

        self._create_document(postings_id=postings_id, document=document)

    def _create_document(self, postings_id: int, document: bytes):
        """
        Creates an entry in the documents table for the posting corresponding to
        `postings_id`.
        """
        query = "INSERT INTO documents (postings_id, document) VALUES (?, ?)"
        with self._connect_to_database() as connection:
            connection.execute(query, [postings_id, document])

    def _create_metadata(self, postings_id: int, metadata: str):
        """
        Creates an entry in the metadata table for the posting corresponding to
        `postings_id`.
        """
        reference, title, superior, deadline = clean_posting_text(metadata)

        query = """
        INSERT INTO metadata (postings_id, reference, title, superior, institution, deadline)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        try:
            with self._connect_to_database() as connection:
                connection.execute(
                    query,
                    [
                        postings_id,
                        reference,
                        title,
                        superior,
                        self.institution,
                        deadline,
                    ],
                )
        except sqlite3.IntegrityError as integrity_error:
            LOGGER.error(integrity_error)

    def _create_posting(self) -> int:
        """Creates an entry in the postings table and returns the primary key."""
        today = date.today().strftime(DATE_FMT)

        query = "INSERT INTO postings (created_at) VALUES (?)"
        with self._connect_to_database() as connection:
            # Connection.execute returns the local cursor which can then be used
            # to acquire the last inserted row's ID (== primary key).
            primary_key = connection.execute(query, [today]).lastrowid
            return primary_key

    def _connect_to_database(self):
        """Connects to SQLite using command line arguments."""
        # Arguments passed via command line aren't visible to Pylint, hence
        # this warning is disabled locally.
        # pylint: disable=no-member
        database_path = str(pathlib.Path(self.database_path))
        connection = sqlite3.connect(database_path)

        return connection
