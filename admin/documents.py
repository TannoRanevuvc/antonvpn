import os
import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, Response

router = APIRouter(prefix="/document")

_DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "media", "documents")
_SAFE_NAME = re.compile(r"^[a-z0-9\-]+$")


@router.get("/style.css")
async def document_css() -> Response:
    path = os.path.join(_DOCS_DIR, "_base.css")
    if not os.path.exists(path):
        raise HTTPException(404)
    with open(path, "r", encoding="utf-8") as f:
        return Response(content=f.read(), media_type="text/css; charset=utf-8")


@router.get("/{name}")
async def serve_document(name: str) -> HTMLResponse:
    if not _SAFE_NAME.match(name):
        raise HTTPException(404)
    path = os.path.join(_DOCS_DIR, f"{name}.html")
    if not os.path.exists(path):
        raise HTTPException(404)
    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())
