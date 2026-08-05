"""Custom AntonVPN subscription page — replaces remnawave/subscription-page container."""
import re
from datetime import datetime, timezone
from pathlib import Path

import aiohttp
from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response

from config import settings

router = APIRouter()

# Path to React SPA build
_WEBAPP_DIST = Path(__file__).parent.parent / "webapp" / "dist"

# User-agents of VPN clients that expect raw subscription data
_VPN_CLIENT_RE = re.compile(
    r"clash|v2ray|shadowrocket|quantumult|surge|hiddify|sing.?box|"
    r"streisand|stash|loon|nekobox|nekoray|karing|flclash|mihomo|xray",
    re.I,
)

_REMNAWAVE_INTERNAL = settings.REMNAWAVE_PANEL_URL.rstrip("/")
_TOKEN = settings.REMNAWAVE_TOKEN


async def _remnawave_get(path: str) -> dict | None:
    url = f"{_REMNAWAVE_INTERNAL}{path}"
    try:
        async with aiohttp.ClientSession() as s:
            resp = await s.get(
                url,
                headers={"Authorization": f"Bearer {_TOKEN}"},
                timeout=aiohttp.ClientTimeout(total=10),
            )
            if resp.status == 200:
                data = await resp.json()
                return data.get("response") if isinstance(data.get("response"), dict) else data
    except Exception:
        pass
    return None


async def _proxy_raw_sub(short_uuid: str) -> Response:
    url = f"{_REMNAWAVE_INTERNAL}/api/sub/{short_uuid}"
    try:
        async with aiohttp.ClientSession() as s:
            resp = await s.get(
                url,
                headers={"Authorization": f"Bearer {_TOKEN}"},
                timeout=aiohttp.ClientTimeout(total=10),
            )
            content = await resp.read()
            ct = resp.headers.get("content-type", "text/plain; charset=utf-8")
            headers = {}
            for h in ("subscription-userinfo", "profile-update-interval", "content-disposition"):
                if h in resp.headers:
                    headers[h] = resp.headers[h]
            return Response(content=content, media_type=ct, headers=headers)
    except Exception:
        return Response(content=b"", status_code=502)


def _fmt_date(iso: str | None) -> str:
    if not iso:
        return ""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y")
    except Exception:
        return iso[:10]


def _days_left(iso: str | None) -> int:
    if not iso:
        return 0
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        delta = dt - datetime.now(timezone.utc)
        return max(0, delta.days)
    except Exception:
        return 0


def _get_support_url() -> str | None:
    try:
        from config import settings as s
        return getattr(s, "SUPPORT_URL", None) or getattr(s, "TG_SUPPORT", None)
    except Exception:
        return None


def _build_sub_url(short_uuid: str) -> str:
    from urllib.parse import urlparse
    parsed = urlparse(settings.ADMIN_PUBLIC_BASE_URL)
    public_base = f"{parsed.scheme}://{parsed.netloc}"
    return f"{public_base}/sub/{short_uuid}"


@router.get("/sub/api/{short_uuid}")
async def subscription_api(short_uuid: str) -> JSONResponse:
    """JSON endpoint consumed by the React SPA."""
    info = await _remnawave_get(f"/api/users/by-short-uuid/{short_uuid}")
    if not info:
        return JSONResponse({"status": "unknown"}, status_code=404)

    raw_status = info.get("status", "UNKNOWN")
    expire_iso = info.get("expireAt")
    days = _days_left(expire_iso)
    support_url = _get_support_url()
    sub_url = _build_sub_url(short_uuid)

    # Map Remnawave status → frontend status
    status = "unknown"
    if raw_status == "ACTIVE":
        status = "expiring" if days <= 3 else "active"
    elif raw_status in ("DISABLED", "EXPIRED"):
        status = "expired"

    return JSONResponse({
        "status": status,
        "expires_at": expire_iso,
        "days_remaining": days,
        "subscription_url": sub_url,
        "support_url": support_url,
    })


@router.get("/sub/{short_uuid}")
async def subscription_page(short_uuid: str, request: Request) -> Response:
    ua = request.headers.get("user-agent", "")

    # VPN clients get raw subscription feed
    if _VPN_CLIENT_RE.search(ua):
        return await _proxy_raw_sub(short_uuid)

    # Browsers get the React SPA
    spa_index = _WEBAPP_DIST / "index.html"
    if spa_index.exists():
        return FileResponse(str(spa_index), media_type="text/html")

    # Fallback to simple HTML if SPA not built
    info = await _remnawave_get(f"/api/users/by-short-uuid/{short_uuid}")
    if not info:
        return HTMLResponse(content=_render_error("Подписка не найдена"), status_code=404)

    expire_iso = info.get("expireAt")
    expire_str = _fmt_date(expire_iso)
    days = _days_left(expire_iso)
    sub_url = _build_sub_url(short_uuid)
    is_active = info.get("status") == "ACTIVE"
    return HTMLResponse(content=_render_fallback(sub_url, expire_str, days, is_active))


def _render_error(msg: str) -> str:
    return f"""<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8">
<title>AntonVPN</title><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{{margin:0;background:#0b0c0f;color:#f4f4ef;font-family:system-ui;
display:flex;align-items:center;justify-content:center;height:100vh;}}
.box{{text-align:center;}}.msg{{color:#a7abb3;margin-top:8px;}}</style></head>
<body><div class="box"><h2>AntonVPN</h2><p class="msg">{msg}</p></div></body></html>"""


def _render_fallback(sub_url: str, expire_str: str, days: int, is_active: bool) -> str:
    status_text = "Активна" if is_active else "Неактивна"
    days_text = f"{days} дн." if days > 0 else "Истекла"
    return f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AntonVPN — Подписка</title>
<style>
body{{margin:0;background:#0b0c0f;color:#f4f4ef;font-family:system-ui;padding:16px}}
.wrap{{max-width:480px;margin:0 auto}}
.card{{background:#17191e;border:1px solid #2b2e35;border-radius:16px;padding:20px;margin-bottom:12px}}
.btn{{display:block;width:100%;padding:14px;background:#c7f36b;color:#15171b;border:none;
border-radius:12px;font-size:14px;font-weight:600;cursor:pointer;text-align:center}}
.url{{word-break:break-all;font-size:12px;color:#a7abb3;margin-bottom:12px}}
</style></head>
<body><div class="wrap">
<h1 style="font-size:20px;margin-bottom:20px">AntonVPN</h1>
<div class="card">
<div>Статус: <b>{status_text}</b></div>
<div>До: {expire_str}</div>
<div>Осталось: {days_text}</div>
</div>
<div class="card">
<div class="url">{sub_url}</div>
<button class="btn" onclick="navigator.clipboard.writeText({repr(sub_url)})">Скопировать ссылку</button>
</div>
</div></body></html>"""
