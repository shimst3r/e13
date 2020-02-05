import argparse
import json
import logging
import pathlib
import typing

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

LOGGER = logging.getLogger(__name__)
TEMPLATES = Jinja2Templates(directory="templates")


async def document_by_id(request: Request) -> Response:
    """Returns the PDF specified by `document_id`."""

    database_path = request.app.state.database_path
    document_id = request.path_params["document_id"]
    document = await _retrieve_document_by_id(
        database_path=database_path, document_id=document_id
    )
    LOGGER.info(_retrieve_document_by_id.cache_info())

    return Response(document, media_type="application/pdf")


async def homepage(request: Request) -> _TemplateResponse:
    """The landing page that presents a list of job postings."""
    database_path = request.app.state.database_path
    query = """
    SELECT id, reference, title, superior, DATE(deadline)
    FROM postings
    ORDER BY DATE(deadline) ASC;
    """
    async with aiosqlite.connect(database_path) as connection:
        async with connection.execute(query) as cursor:
            postings = await cursor.fetchall()

    return TEMPLATES.TemplateResponse(
        "index.html", {"request": request, "postings": postings}
    )


def _build_app(database_path: str) -> Starlette:
    routes = [
        Route("/", homepage),
        Route("/documents/{document_id:int}", document_by_id, name="documents"),
        Mount("/static", app=StaticFiles(directory="static"), name="static"),
    ]
    _app = Starlette(debug=True, routes=routes)
    _app.state.database_path = str(pathlib.Path(database_path))

    return _app


@async_lru.alru_cache(maxsize=32)
async def _retrieve_document_by_id(
    database_path: str, document_id: int
) -> typing.AsyncGenerator[bytes, None]:
    query = """
    SELECT document
    FROM postings
    WHERE id = ?
    """
    async with aiosqlite.connect(database_path) as connection:
        async with connection.execute(query, [document_id]) as cursor:
            document = await cursor.fetchone()

    return document[0]


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(description="Project e13 server.")
    PARSER.add_argument(
        "database_path", type=str, help="database path to sqlite3 instance",
    )
    ARGS = PARSER.parse_args()

    APP = _build_app(database_path=ARGS.database_path)
    uvloop.install()
    uvicorn.run(APP, host="127.0.0.1", port=5000, log_level="info")
