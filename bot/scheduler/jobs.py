"""APScheduler job definitions."""
from __future__ import annotations

from aiogram import Bot
from aiogram_dialog import BgManagerFactory
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import logger
from database.confdb import async_session_factory


async def check_expiry_notifications(bot: Bot, bg_factory: BgManagerFactory) -> None:
    """Send expiry notifications 3d / 1d / 1h before subscription end."""
    async with async_session_factory() as session:
        from services.subscription_service import SubscriptionService
        from services.notification_service import NotificationService
        from bot.states import NotifySG
        from aiogram_dialog import StartMode
        from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
        from database.repositories import UserRepository

        svc = SubscriptionService(session)
        notify_svc = NotificationService(session)
        user_repo = UserRepository(session)
        rules = await notify_svc.get_active_rules()

        state_map = {72: NotifySG.EXPIRY_3D, 24: NotifySG.EXPIRY_1D, 1: NotifySG.EXPIRY_1H}

        for rule in rules:
            target_state = state_map.get(rule.hours_before_expiry)
            if target_state is None:
                continue

            subs = await svc.get_expiring_without_flag(rule.hours_before_expiry)
            for sub in subs:
                user = await user_repo.get_by_id(sub.user_id)
                if not user or user.blocked_bot or user.is_banned:
                    continue
                try:
                    bg = bg_factory.bg(bot, user.telegram_id, user.chat_id)
                    await bg.start(target_state, mode=StartMode.RESET_STACK)
                    await svc.mark_notify_flag(sub, rule.hours_before_expiry)
                except TelegramForbiddenError:
                    from services.user_service import UserService
                    await UserService(session).set_blocked_bot(user, True)
                except TelegramBadRequest as exc:
                    logger.warning("TelegramBadRequest for user %s: %s", user.telegram_id, exc)
                except Exception as exc:
                    logger.error("Notify error for sub %s: %s", sub.id, exc)


async def handle_expired_subscriptions(bot: Bot, bg_factory: BgManagerFactory) -> None:
    """Mark expired subscriptions and notify users."""
    async with async_session_factory() as session:
        from services.subscription_service import SubscriptionService
        from bot.states import NotifySG
        from aiogram_dialog import StartMode
        from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
        from database.repositories import UserRepository

        svc = SubscriptionService(session)
        user_repo = UserRepository(session)
        expired_subs = await svc.get_just_expired()

        for sub in expired_subs:
            user = await user_repo.get_by_id(sub.user_id)
            await svc.mark_expired(sub)

            if not user or user.blocked_bot or user.is_banned:
                continue
            try:
                bg = bg_factory.bg(bot, user.telegram_id, user.chat_id)
                await bg.start(NotifySG.EXPIRED, mode=StartMode.RESET_STACK)
            except TelegramForbiddenError:
                from services.user_service import UserService
                await UserService(session).set_blocked_bot(user, True)
            except Exception as exc:
                logger.error("Expired notify error for sub %s: %s", sub.id, exc)


async def process_auto_renewals(bot: Bot, bg_factory: BgManagerFactory) -> None:
    """Auto-renew subscriptions for users with sufficient balance."""
    async with async_session_factory() as session:
        from services.subscription_service import SubscriptionService
        from services.user_service import UserService, InsufficientBalanceError
        from database.repositories import UserRepository

        svc = SubscriptionService(session)
        user_svc = UserService(session)
        user_repo = UserRepository(session)
        due = await svc.get_due_for_auto_renewal()

        for sub in due:
            user = await user_repo.get_by_id(sub.user_id)
            if not user:
                continue
            try:
                await svc.renew(sub, user)
                logger.info("Auto-renewed sub %s for user %s", sub.id, user.telegram_id)
            except InsufficientBalanceError:
                # Disable auto-renewal and notify
                sub = await svc.toggle_auto_renewal(sub, user.id)
                try:
                    from aiogram.exceptions import TelegramForbiddenError
                    await bot.send_message(
                        user.chat_id,
                        "❌ Автопродление отключено — недостаточно средств на балансе. Пополните баланс или продлите вручную.",
                    )
                except Exception:
                    pass
            except Exception as exc:
                logger.error("Auto-renewal failed for sub %s: %s", sub.id, exc)


async def expire_old_gifts() -> None:
    async with async_session_factory() as session:
        from services.gift_service import GiftService
        count = await GiftService(session).expire_old()
        if count:
            logger.info("Expired %d old gifts", count)


async def expire_old_topups() -> None:
    async with async_session_factory() as session:
        from services.payment_service import PaymentService
        count = await PaymentService(session).expire_old_topups()
        if count:
            logger.info("Expired %d old topups", count)


def register_jobs(scheduler: AsyncIOScheduler, bot: Bot, bg_factory: BgManagerFactory) -> None:
    scheduler.add_job(
        check_expiry_notifications, "interval", minutes=30,
        args=[bot, bg_factory], id="check_expiry_notifications",
    )
    scheduler.add_job(
        handle_expired_subscriptions, "interval", minutes=30,
        args=[bot, bg_factory], id="handle_expired_subscriptions",
    )
    scheduler.add_job(
        process_auto_renewals, "interval", hours=1,
        args=[bot, bg_factory], id="process_auto_renewals",
    )
    scheduler.add_job(
        expire_old_gifts, "cron", hour=3, minute=0, id="expire_old_gifts",
    )
    scheduler.add_job(
        expire_old_topups, "interval", minutes=15, id="expire_old_topups",
    )
