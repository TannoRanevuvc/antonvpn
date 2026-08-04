"""Admin broadcast view: send messages to all or segmented users."""
import asyncio
from datetime import datetime, timedelta

from sqladmin import BaseView, expose
from starlette.requests import Request
from starlette.responses import HTMLResponse

from database.confdb import async_session_factory
from config import logger, settings

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
                select(User.telegram_id, User.chat_id).where(User.is_banned == False, User.blocked_bot == False)
            )
        elif segment == "active_vpn":
            result = await session.execute(
                select(User.telegram_id, User.chat_id).join(
                    Subscription, Subscription.user_id == User.id
                ).where(
                    Subscription.remna_status == RemnaStatus.ACTIVE,
                    Subscription.tariff_type == TariffType.VPN,
                    User.is_banned == False,
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
                )
            )
        elif segment == "expiring_3d":
            result = await session.execute(
                select(User.telegram_id, User.chat_id).join(
                    Subscription, Subscription.user_id == User.id
                ).where(
                    Subscription.expires_at.between(now, now + timedelta(days=3)),
                    Subscription.remna_status == RemnaStatus.ACTIVE,
                )
            )
        elif segment == "no_sub":
            result = await session.execute(
                select(User.telegram_id, User.chat_id).where(
                    ~User.id.in_(select(Subscription.user_id)),
                    User.is_banned == False,
                )
            )
        else:
            result = await session.execute(
                select(User.telegram_id, User.chat_id).where(User.is_banned == False)
            )

        return list(result.all())


async def _send_broadcast(job_id: str, bot, users: list[tuple], text: str) -> None:
    from aiogram.exceptions import TelegramForbiddenError
    sent = 0
    failed = 0
    total = len(users)
    _progress[job_id] = {"sent": 0, "failed": 0, "total": total, "done": False}

    for tg_id, chat_id in users:
        try:
            await bot.send_message(chat_id, text, parse_mode="HTML")
            sent += 1
        except TelegramForbiddenError:
            failed += 1
            async with async_session_factory() as session:
                from database.repositories import UserRepository
                repo = UserRepository(session)
                user = await repo.get_by_chat_id(chat_id)
                if user:
                    user.blocked_bot = True
                    await repo.save(user)
        except Exception as exc:
            logger.warning("Broadcast failed for %s: %s", chat_id, exc)
            failed += 1

        _progress[job_id]["sent"] = sent
        _progress[job_id]["failed"] = failed
        await asyncio.sleep(0.05)  # ~20 msg/s Telegram rate limit

    _progress[job_id]["done"] = True
    logger.info("Broadcast %s complete: sent=%d failed=%d", job_id, sent, failed)


class BroadcastView(BaseView):
    name = "Рассылка"
    icon = "fa-solid fa-bullhorn"
    _bot = None

    @classmethod
    def set_bot(cls, bot) -> None:
        cls._bot = bot

    @expose("/admin/broadcast", methods=["GET", "POST"])
    async def broadcast(self, request: Request):
        message = ""
        if request.method == "POST":
            form = await request.form()
            text = form.get("text", "").strip()
            segment = form.get("segment", "all")

            if text and self._bot:
                users = await _get_segment_users(segment)
                import uuid
                job_id = str(uuid.uuid4())[:8]
                asyncio.create_task(_send_broadcast(job_id, self._bot, users, text))
                message = f"✅ Рассылка #{job_id} запущена для {len(users)} пользователей."
            else:
                message = "⚠️ Введите текст сообщения."

        return await self.templates.TemplateResponse(
            request,
            "sqladmin/broadcast.html",
            {"message": message, "progress": _progress},
        )
