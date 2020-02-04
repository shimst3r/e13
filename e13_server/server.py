import json
import pathlib

import aiosqlite
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route


async def homepage(request: Request):
    database_path = request.app.state.database_path
    query = """
    SELECT id, reference, title, superior, DATE(deadline)
    FROM postings
    ORDER BY DATE(deadline) ASC;
    """
    async with aiosqlite.connect(database_path) as connection:
        data = await connection.execute(query)

    return JSONResponse({"data": json.dumps(data)})


def build_app(database_path):
    app = Starlette(debug=True, routes=[Route("/", homepage),])
    app.state.database_path = str(pathlib.Path(database_path))
