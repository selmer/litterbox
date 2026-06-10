from pathlib import Path

from fastapi import Request
from fastapi.responses import FileResponse


FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"


def wants_frontend_document(request: Request) -> bool:
    accept = request.headers.get("accept", "").lower()
    return "text/html" in accept and "application/json" not in accept


def frontend_index_response() -> FileResponse | None:
    index_file = FRONTEND_DIST / "index.html"
    if not index_file.is_file():
        return None
    return FileResponse(index_file)
