import argparse
import json
import pathlib

import aiosqlite
import uvicorn
import uvloop
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")


async def homepage(request: Request) -> Jinja2Templates.TemplateResponse:
    database_path = request.app.state.database_path
    query = """
    SELECT id, reference, title, superior, DATE(deadline)
    FROM postings
    ORDER BY DATE(deadline) ASC;
    """
    async with aiosqlite.connect(database_path) as connection:
        async with connection.execute(query) as cursor:
            postings = await cursor.fetchall()

    return templates.TemplateResponse(
        "index.html", {"request": request, "postings": postings}
    )


async def documents(request: Request) -> Response:
    database_path = request.app.state.database_path
    document_id = request.path_params["document_id"]
    query = """
    SELECT document
    FROM postings
    WHERE id = ?
    """
    async with aiosqlite.connect(database_path) as connection:
        async with connection.execute(query, [document_id]) as cursor:
            document = await cursor.fetchone()

    return Response(document[0], media_type="application/pdf")


def build_app(database_path: str) -> Starlette:
    routes = [
        Route("/", homepage),
        Route("/documents/{document_id:int}", documents, name="documents"),
        Mount("/static", app=StaticFiles(directory="static"), name="static"),
    ]
    _app = Starlette(debug=True, routes=routes)
    _app.state.database_path = str(pathlib.Path(database_path))

    return _app


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Project e13 server.")
    parser.add_argument(
        "database_path", type=str, help="database path to sqlite3 instance",
    )
    args = parser.parse_args()

    app = build_app(database_path=args.database_path)
    uvloop.install()
    uvicorn.run(app, host="127.0.0.1", port=5000, log_level="info")
