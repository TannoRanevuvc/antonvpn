"""Admin broadcast view: send messages to all or segmented users."""
import asyncio
import uuid
from datetime import datetime, timedelta

import aiohttp
from sqladmin import BaseView, expose
from starlette.requests import Request

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
    photo_url: str | None = None,
    btn_text: str | None = None,
    btn_url: str | None = None,
) -> None:
    sent = 0
    failed = 0
    total = len(users)
    _progress[job_id] = {"sent": 0, "failed": 0, "total": total, "done": False}
    proxy = settings.SOCKS5_PROXY_URL or None

    reply_markup = None
    if btn_text and btn_url:
        reply_markup = {"inline_keyboard": [[{"text": btn_text, "url": btn_url}]]}

    connector = aiohttp.TCPConnector()
    async with aiohttp.ClientSession(connector=connector) as http:
        for _tg_id, chat_id in users:
            try:
                if photo_url:
                    payload = {
                        "chat_id": chat_id,
                        "photo": photo_url,
                        "caption": text,
                        "parse_mode": "HTML",
                    }
                    if reply_markup:
                        payload["reply_markup"] = reply_markup
                    resp = await http.post(
                        f"{_TG_API}/sendPhoto",
                        json=payload,
                        proxy=proxy,
                        timeout=aiohttp.ClientTimeout(total=15),
                    )
                else:
                    payload = {
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": "HTML",
                    }
                    if reply_markup:
                        payload["reply_markup"] = reply_markup
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
        message = ""
        if request.method == "POST":
            form = await request.form()
            text = form.get("text", "").strip()
            segment = form.get("segment", "all")
            photo_url = form.get("photo_url", "").strip() or None
            btn_text = form.get("btn_text", "").strip() or None
            btn_url = form.get("btn_url", "").strip() or None

            if text:
                users = await _get_segment_users(segment)
                job_id = str(uuid.uuid4())[:8]
                asyncio.create_task(
                    _send_broadcast(job_id, users, text, photo_url, btn_text, btn_url)
                )
                message = f"✅ Рассылка #{job_id} запущена для {len(users)} пользователей."
            else:
                message = "⚠️ Введите текст сообщения."

        return await self.templates.TemplateResponse(
            request,
            "sqladmin/broadcast.html",
            {"message": message, "progress": _progress},
        )
