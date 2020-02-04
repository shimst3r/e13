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


class BielefeldUniversitySpider(scrapy.Spider):
    name = "bielefeld_university"
    start_urls = [f"{BASE_URL}/auswiss_2013.html/"]

    def parse(self, response):
        # Line breaks make accessing content via CSS selectors more difficult,
        # hence they're removed.
        response = response.replace(body=response.body.replace(b"<br>", b""))

        for posting in response.css("a.intern"):
            try:
                pdf_url = posting.attrib["href"]
                metadata = clean_posting_text(posting.css("::text").get())
            except KeyError as key_error:
                LOGGER.error(key_error)
            else:
                yield scrapy.Request(
                    f"{BASE_URL}/{pdf_url}",
                    callback=self.parse_pdf,
                    cb_kwargs={"metadata": metadata},
                )

    def parse_pdf(self, response, metadata):
        """
        Retrieve a job postings PDF and insert it into the database using
        available metadata.
        """
        # Arguments passed via command line aren't visible to Pylint, hence
        # this warning is disabled locally.
        # pylint: disable=no-member
        database_path = str(pathlib.Path(self.database_path))
        query = """
        INSERT INTO postings (reference, title, superior, deadline, created_at, document)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        today = date.today().strftime(DATE_FMT)

        with sqlite3.connect(database_path) as conn:
            result = conn.execute(query, [*metadata, today, response.body])

        LOGGER.info(f"Added postings entry {result}.")


def clean_posting_text(text: str) -> typing.Optional[typing.List[str]]:
    try:
        reference, title, superior, deadline = text.split("\n\n")
        if match := re.search(r"wiss\d+", reference):
            reference = match.group()
        if match := re.search(r"\d{2}.\d{2}.\d{4}", deadline):
            deadline = match.group()
    except ValueError as value_error:
        LOGGER.error(value_error)
        return None
    else:
        return [reference, title, superior, deadline]
