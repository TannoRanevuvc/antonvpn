import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram_dialog import setup_dialogs
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.dialogs import get_all_dialogs
from bot.handlers import errors_router, start_router
from bot.middlewares import DBSessionMiddleware, LanguageMiddleware, UserContextMiddleware
from bot.scheduler.jobs import register_jobs
from config import settings, logger


async def main() -> None:
    session_kwargs = {}
    if settings.SOCKS5_PROXY_URL:
        session_kwargs["proxy"] = settings.SOCKS5_PROXY_URL

    bot = Bot(
        token=settings.TOKEN_BOT_TG,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        session=AiohttpSession(**session_kwargs),
    )

    dp = Dispatcher(storage=MemoryStorage())

    # Middlewares (order: DB → User → Language)
    dp.update.outer_middleware(DBSessionMiddleware())
    dp.update.outer_middleware(UserContextMiddleware())
    dp.update.outer_middleware(LanguageMiddleware())

    # Routers
    dp.include_router(start_router)
    dp.include_router(errors_router)

    # Dialogs
    for dialog in get_all_dialogs():
        dp.include_router(dialog)

    bg_factory = setup_dialogs(dp)

    # Scheduler
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    register_jobs(scheduler, bot, bg_factory)
    scheduler.start()

    logger.info("Bot starting...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown()
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
