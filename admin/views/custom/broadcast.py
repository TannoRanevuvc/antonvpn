"""Admin broadcast view: send messages to all or segmented users."""
import asyncio
import uuid
from datetime import datetime, timedelta

import aiohttp
from sqladmin import BaseView, expose
from starlette.requests import Request
from starlette.responses import RedirectResponse

from database.confdb import async_session_factory
from config import logger, settings

_TG_API = f"https://api.telegram.org/bot{settings.TOKEN_BOT_TG}"

_progress: dict = {}


async def _get_segment_users(segment: str) -> list[tuple[int, int]]:
    """Returns list of (telegram_id, chat_id) tuples for a segment."""
    from sqlalchemy import select
    from database.models.user import User
    from database.models.subscription import Subscription, RemnaStatus, TariffType

    async with async_session_factory() as session:
        now = datetime.utcnow()

        if segment == "all":
            result = await session.execute(
                select(User.telegram_id, User.chat_id).where(
                    User.is_banned == False, User.blocked_bot == False
                )
            )
        elif segment == "active_vpn":
            result = await session.execute(
                select(User.telegram_id, User.chat_id).join(
                    Subscription, Subscription.user_id == User.id
                ).where(
                    Subscription.remna_status == RemnaStatus.ACTIVE,
                    Subscription.tariff_type == TariffType.VPN,
                    User.is_banned == False,
                    User.blocked_bot == False,
                )
            )
        elif segment == "active_obfs":
            result = await session.execute(
                select(User.telegram_id, User.chat_id).join(
                    Subscription, Subscription.user_id == User.id
                ).where(
                    Subscription.remna_status == RemnaStatus.ACTIVE,
                    Subscription.tariff_type == TariffType.OBFUSCATED,
                    User.is_banned == False,
                    User.blocked_bot == False,
                )
            )
        elif segment == "active_any":
            result = await session.execute(
                select(User.telegram_id, User.chat_id).join(
                    Subscription, Subscription.user_id == User.id
                ).where(
                    Subscription.remna_status == RemnaStatus.ACTIVE,
                    User.is_banned == False,
                    User.blocked_bot == False,
                ).distinct()
            )
        elif segment == "expiring_3d":
            result = await session.execute(
                select(User.telegram_id, User.chat_id).join(
                    Subscription, Subscription.user_id == User.id
                ).where(
                    Subscription.expires_at.between(now, now + timedelta(days=3)),
                    Subscription.remna_status == RemnaStatus.ACTIVE,
                    User.blocked_bot == False,
                )
            )
        elif segment == "expiring_7d":
            result = await session.execute(
                select(User.telegram_id, User.chat_id).join(
                    Subscription, Subscription.user_id == User.id
                ).where(
                    Subscription.expires_at.between(now, now + timedelta(days=7)),
                    Subscription.remna_status == RemnaStatus.ACTIVE,
                    User.blocked_bot == False,
                )
            )
        elif segment == "expired":
            result = await session.execute(
                select(User.telegram_id, User.chat_id).join(
                    Subscription, Subscription.user_id == User.id
                ).where(
                    Subscription.remna_status == RemnaStatus.DISABLED,
                    User.is_banned == False,
                    User.blocked_bot == False,
                ).distinct()
            )
        elif segment == "no_sub":
            result = await session.execute(
                select(User.telegram_id, User.chat_id).where(
                    ~User.id.in_(select(Subscription.user_id)),
                    User.is_banned == False,
                    User.blocked_bot == False,
                )
            )
        elif segment == "has_balance":
            from sqlalchemy import cast
            from sqlalchemy import Numeric
            result = await session.execute(
                select(User.telegram_id, User.chat_id).where(
                    User.balance_rub > 0,
                    User.is_banned == False,
                    User.blocked_bot == False,
                )
            )
        elif segment == "new_7d":
            result = await session.execute(
                select(User.telegram_id, User.chat_id).where(
                    User.created_at >= now - timedelta(days=7),
                    User.is_banned == False,
                    User.blocked_bot == False,
                )
            )
        elif segment == "new_30d":
            result = await session.execute(
                select(User.telegram_id, User.chat_id).where(
                    User.created_at >= now - timedelta(days=30),
                    User.is_banned == False,
                    User.blocked_bot == False,
                )
            )
        elif segment == "inactive_30d":
            result = await session.execute(
                select(User.telegram_id, User.chat_id).where(
                    User.last_activity < now - timedelta(days=30),
                    User.is_banned == False,
                    User.blocked_bot == False,
                )
            )
        else:
            result = await session.execute(
                select(User.telegram_id, User.chat_id).where(
                    User.is_banned == False, User.blocked_bot == False
                )
            )

        return list(result.all())


async def _send_broadcast(
    job_id: str,
    users: list[tuple],
    text: str,
    photo_bytes: bytes | None = None,
    photo_filename: str = "photo.jpg",
    btn_text: str | None = None,
    btn_url: str | None = None,
) -> None:
    import json as _json

    sent = 0
    failed = 0
    total = len(users)
    _progress[job_id] = {"sent": 0, "failed": 0, "total": total, "done": False}
    proxy = settings.SOCKS5_PROXY_URL or None

    reply_markup_str = None
    if btn_text and btn_url:
        reply_markup_str = _json.dumps({"inline_keyboard": [[{"text": btn_text, "url": btn_url}]]})

    connector = aiohttp.TCPConnector()
    async with aiohttp.ClientSession(connector=connector) as http:
        for _tg_id, chat_id in users:
            try:
                if photo_bytes:
                    form = aiohttp.FormData()
                    form.add_field("chat_id", str(chat_id))
                    form.add_field("caption", text)
                    form.add_field("parse_mode", "HTML")
                    if reply_markup_str:
                        form.add_field("reply_markup", reply_markup_str)
                    form.add_field(
                        "photo", photo_bytes,
                        filename=photo_filename,
                        content_type="image/jpeg",
                    )
                    resp = await http.post(
                        f"{_TG_API}/sendPhoto",
                        data=form,
                        proxy=proxy,
                        timeout=aiohttp.ClientTimeout(total=30),
                    )
                else:
                    payload = {
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": "HTML",
                    }
                    if reply_markup_str:
                        payload["reply_markup"] = _json.loads(reply_markup_str)
                    resp = await http.post(
                        f"{_TG_API}/sendMessage",
                        json=payload,
                        proxy=proxy,
                        timeout=aiohttp.ClientTimeout(total=10),
                    )

                data = await resp.json()
                if data.get("ok"):
                    sent += 1
                else:
                    err = data.get("description", "")
                    if "bot was blocked" in err or "user is deactivated" in err or "chat not found" in err:
                        async with async_session_factory() as session:
                            from database.repositories import UserRepository
                            user = await UserRepository(session).get_by_chat_id(chat_id)
                            if user:
                                user.blocked_bot = True
                                await UserRepository(session).save(user)
                    failed += 1
            except Exception as exc:
                logger.warning("Broadcast failed for chat_id=%s: %s", chat_id, exc)
                failed += 1

            _progress[job_id]["sent"] = sent
            _progress[job_id]["failed"] = failed
            await asyncio.sleep(0.05)  # ~20 msg/s

    _progress[job_id]["done"] = True
    logger.info("Broadcast %s done: sent=%d failed=%d", job_id, sent, failed)


class BroadcastView(BaseView):
    name = "Рассылка"
    icon = "fa-solid fa-bullhorn"

    @expose("/broadcast", methods=["GET", "POST"])
    async def broadcast(self, request: Request):
        if request.method == "POST":
            form = await request.form()
            text = form.get("text", "").strip()
            segment = form.get("segment", "all")
            btn_text = form.get("btn_text", "").strip() or None
            btn_url = form.get("btn_url", "").strip() or None

            if not text:
                return RedirectResponse(
                    url=str(request.url).split("?")[0] + "?error=empty",
                    status_code=303,
                )

            photo_bytes = None
            photo_filename = "photo.jpg"
            photo_file = form.get("photo")
            if photo_file and hasattr(photo_file, "read"):
                photo_bytes = await photo_file.read()
                if not photo_bytes:
                    photo_bytes = None
                else:
                    photo_filename = photo_file.filename or "photo.jpg"

            users = await _get_segment_users(segment)
            job_id = str(uuid.uuid4())[:8]
            asyncio.create_task(
                _send_broadcast(job_id, users, text, photo_bytes, photo_filename, btn_text, btn_url)
            )
            return RedirectResponse(
                url=str(request.url).split("?")[0] + f"?ok={job_id}&count={len(users)}",
                status_code=303,
            )

        message = ""
        msg_type = "success"
        if "ok" in request.query_params:
            job_id = request.query_params["ok"]
            count = request.query_params.get("count", "?")
            message = f"✅ Рассылка #{job_id} запущена для {count} пользователей."
        elif "error" in request.query_params:
            message = "⚠️ Введите текст сообщения."
            msg_type = "warning"

        return await self.templates.TemplateResponse(
            request,
            "sqladmin/broadcast.html",
            {"message": message, "msg_type": msg_type, "progress": _progress},
        )
