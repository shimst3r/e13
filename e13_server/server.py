import argparse
import json
import logging
import pathlib
import typing
from datetime import date

import aiosqlite
import async_lru
import uvicorn
import uvloop
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.templating import _TemplateResponse, Jinja2Templates

DATE_FMT = "%Y-%m-%d"
LOGGER = logging.getLogger(__name__)
TEMPLATES = Jinja2Templates(directory="templates")


async def document_by_id(request: Request) -> Response:
    """Returns the PDF specified by `document_id`."""

    database_path = request.app.state.database_path
    postings_id = request.path_params["postings_id"]
    document = await _retrieve_document_by_id(
        database_path=database_path, postings_id=postings_id
    )
    LOGGER.info(_retrieve_document_by_id.cache_info())

    return Response(document, media_type="application/pdf")


async def homepage(request: Request) -> _TemplateResponse:
    """The landing page that presents a list of job postings."""
    database_path = request.app.state.database_path
    today = date.today().strftime(DATE_FMT)

    query = """
    SELECT postings_id, title, superior, institution, date(deadline)
    FROM metadata
    WHERE date(deadline) >= ?
    ORDER BY date(deadline) ASC;
    """
    async with aiosqlite.connect(database_path) as connection:
        async with connection.execute(query, [today]) as cursor:
            postings = await cursor.fetchall()

    return TEMPLATES.TemplateResponse(
        "index.html", {"request": request, "postings": postings}
    )


async def result_page(request: Request) -> _TemplateResponse:
    """The result page for keyword searches."""
    database_path = request.app.state.database_path
    keyword = request.query_params["search_keyword"]
    today = date.today().strftime(DATE_FMT)

    postings = await _filter_postings_by_keyword(
        database_path=database_path, keyword=keyword, date=today
    )
    return TEMPLATES.TemplateResponse(
        "index.html", {"request": request, "postings": postings}
    )


def _build_app(database_path: str) -> Starlette:
    routes = [
        Route("/", homepage),
        Route("/documents/{postings_id:int}", document_by_id, name="documents"),
        Route("/results", result_page, name="results"),
        Mount("/static", app=StaticFiles(directory="static"), name="static"),
    ]
    _app = Starlette(debug=True, routes=routes)
    _app.state.database_path = str(pathlib.Path(database_path))

    return _app


@async_lru.alru_cache(maxsize=32)
async def _filter_postings_by_keyword(
    database_path: str, keyword: str, date: str
) -> typing.Awaitable[typing.List]:
    query = """
    SELECT m.postings_id, m.title, m.superior, m.institution, date(m.deadline)
    FROM metadata m
    INNER JOIN fulltexts f
    ON m.postings_id = f.postings_id
    WHERE date(m.deadline) >= ? AND f.text MATCH ?
    ORDER BY date(m.deadline) ASC;
    """
    async with aiosqlite.connect(database_path) as connection:
        async with connection.execute(query, [date, keyword]) as cursor:
            return await cursor.fetchall()


@async_lru.alru_cache(maxsize=32)
async def _retrieve_document_by_id(
    database_path: str, postings_id: int
) -> typing.AsyncGenerator[bytes, None]:
    query = """
    SELECT document
    FROM documents
    WHERE postings_id = ?
    ORDER BY document ASC, postings_id ASC
    """
    async with aiosqlite.connect(database_path) as connection:
        async with connection.execute(query, [postings_id]) as cursor:
            document = await cursor.fetchone()

    return document[0]


APP = _build_app(database_path="../postings.db")

if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(description="Project e13 server.")
    PARSER.add_argument(
        "database_path", type=str, help="database path to sqlite3 instance",
    )
    ARGS = PARSER.parse_args()

    APP = _build_app(database_path=ARGS.database_path)
    uvloop.install()
    uvicorn.run(APP, host="127.0.0.1", port=5000, log_level="info")
