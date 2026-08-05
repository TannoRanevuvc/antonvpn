import os
import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from database.confdb import async_session_maker
from database.repositories.document import LegalDocumentRepository

router = APIRouter(prefix="/document")

_DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "media", "documents")
_SAFE_NAME = re.compile(r"^[a-z0-9\-]+$")

_CSS_CACHE: str | None = None


@router.get("/style.css")
async def document_css() -> Response:
    global _CSS_CACHE
    if _CSS_CACHE is None:
        path = os.path.join(_DOCS_DIR, "_base.css")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                _CSS_CACHE = f.read()
        else:
            _CSS_CACHE = ""
    return Response(content=_CSS_CACHE, media_type="text/css; charset=utf-8")


@router.get("/{slug}")
async def serve_document(slug: str) -> HTMLResponse:
    if not _SAFE_NAME.match(slug):
        raise HTTPException(404)

    # Try DB first
    async with async_session_maker() as session:
        repo = LegalDocumentRepository(session)
        doc = await repo.get_by_slug(slug)

    if doc:
        return HTMLResponse(content=_wrap_content(doc.title, doc.html_content))

    # Fallback: static file
    path = os.path.join(_DOCS_DIR, f"{slug}.html")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())

    raise HTTPException(404)


def _wrap_content(title: str, html_content: str) -> str:
    """If the content is a full HTML document, return as-is. Otherwise wrap in layout."""
    stripped = html_content.lstrip()
    if stripped.lower().startswith("<!doctype") or stripped.lower().startswith("<html"):
        return html_content
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — AntonVPN</title>
<link rel="stylesheet" href="/document/style.css">
</head>
<body>
<div class="wrap">
  <div class="logo">
    <div class="logo-icon">🔒</div>
    <span class="logo-name">AntonVPN</span>
  </div>
  <h1>{title}</h1>
  {html_content}
  <div class="footer">© 2026 AntonVPN. Все права защищены.</div>
</div>
</body>
</html>"""
