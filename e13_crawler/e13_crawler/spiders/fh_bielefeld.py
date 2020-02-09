# -*- coding: utf-8 -*-
import logging
import pathlib
import sqlite3
from datetime import date

import scrapy

BASE_URL = "https://www.fh-bielefeld.de/jobs/"
DATE_FMT = "%Y-%m-%d"
FILTER = "Wissenschaftliche Mitarbeiterin / Wissenschaftlicher Mitarbeiter"
LOGGER = logging.getLogger(__name__)


class FhBielefeldSpider(scrapy.Spider):
    name = "fh_bielefeld"
    institution = "FH Bielefeld"
    start_urls = [BASE_URL]

    def parse(self, response):
        parent_node = response.xpath(f'//*[text()[contains(.,"{FILTER}")]]/..')

        for job_offer in parent_node.css("div.job_offer"):
            postings_id = self._create_posting()
            title = job_offer.css("div.shortdesc::text").get()
            breakpoint()
            LOGGER.info(postings_id, title)

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
