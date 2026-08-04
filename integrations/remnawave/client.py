"""Async HTTP client for the Remnawave VPN panel API."""
import asyncio
from datetime import datetime
from typing import Any, Sequence

import aiohttp

from config import settings
from .exceptions import RemnawaveApiError

_ALLOWED_STATUSES = {"ACTIVE", "DISABLED"}
_TIMEOUT = aiohttp.ClientTimeout(total=25)


def _headers() -> dict:
    token = settings.REMNAWAVE_TOKEN
    if not token.lower().startswith("bearer "):
        token = f"Bearer {token}"
    return {
        "Authorization": token,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _api_base() -> str:
    return f"{settings.REMNAWAVE_PANEL_URL.rstrip('/')}/api"


def _sanitize_status(status: str | None) -> str:
    if status and status.upper() in _ALLOWED_STATUSES:
        return status.upper()
    return "ACTIVE"


async def _request(
    method: str,
    path: str,
    *,
    json_body: dict | None = None,
    session: aiohttp.ClientSession | None = None,
) -> dict:
    url = f"{_api_base()}{path}"
    _own_session = session is None
    if _own_session:
        session = aiohttp.ClientSession(timeout=_TIMEOUT)
    try:
        async with session.request(method, url, json=json_body, headers=_headers()) as resp:
            try:
                data = await resp.json(content_type=None)
            except Exception:
                data = {}
            if resp.status >= 400:
                raise RemnawaveApiError(
                    message=str(data),
                    status=resp.status,
                    url=url,
                    response=data,
                )
            return data
    except asyncio.TimeoutError:
        raise RemnawaveApiError(f"Timeout calling {url}", url=url)
    except aiohttp.ClientError as exc:
        raise RemnawaveApiError(str(exc), url=url)
    finally:
        if _own_session and session:
            await session.close()


async def create_user(
    username: str,
    expires_at: datetime | None = None,
    status: str = "ACTIVE",
    active_internal_squad_uuids: Sequence[str] | None = None,
    traffic_limit_bytes: int | None = None,
    session: aiohttp.ClientSession | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "username": username,
        "status": _sanitize_status(status),
    }
    if expires_at:
        body["expireAt"] = expires_at.isoformat()
    if active_internal_squad_uuids:
        body["activeInternalSquads"] = list(active_internal_squad_uuids)
    if traffic_limit_bytes is not None:
        body["trafficLimitBytes"] = traffic_limit_bytes

    try:
        data = await _request("POST", "/users", json_body=body, session=session)
    except RemnawaveApiError as exc:
        # A019: username already exists — fetch and return existing
        resp = exc.response
        error_code = resp.get("code") or (resp.get("errors") or [{}])[0].get("code", "")
        if str(error_code) == "A019":
            return await get_user_by_username(username, session=session)
        raise

    return data


async def update_user(
    user_uuid: str,
    status: str | None = None,
    expires_at: datetime | None = None,
    active_internal_squad_uuids: Sequence[str] | None = None,
    session: aiohttp.ClientSession | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {"uuid": user_uuid}
    if status is not None:
        body["status"] = _sanitize_status(status)
    if expires_at is not None:
        body["expireAt"] = expires_at.isoformat()
    if active_internal_squad_uuids is not None:
        body["activeInternalSquads"] = list(active_internal_squad_uuids)
    return await _request("PATCH", "/users", json_body=body, session=session)


async def get_user(user_uuid: str, session: aiohttp.ClientSession | None = None) -> dict[str, Any]:
    return await _request("GET", f"/users/{user_uuid}", session=session)


async def get_user_by_username(username: str, session: aiohttp.ClientSession | None = None) -> dict[str, Any]:
    return await _request("GET", f"/users/by-username/{username}", session=session)


async def list_user_devices(user_uuid: str, session: aiohttp.ClientSession | None = None) -> list[dict]:
    data = await _request("GET", f"/users/{user_uuid}", session=session)
    # Remnawave returns devices inside the user object
    return data.get("onlineDevices") or data.get("devices") or []


async def delete_device(user_uuid: str, device_id: str, session: aiohttp.ClientSession | None = None) -> dict:
    return await _request("DELETE", f"/users/{user_uuid}/devices/{device_id}", session=session)
