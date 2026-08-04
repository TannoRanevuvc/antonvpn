from aiogram import Router
from aiogram.types import ErrorEvent
from aiogram_dialog import DialogManager, StartMode

from bot.states import CabinetSG
from config import logger

router = Router()


@router.errors()
async def error_handler(event: ErrorEvent, dialog_manager: DialogManager | None = None) -> None:
    logger.error("Unhandled error: %s", event.exception, exc_info=event.exception)
    if dialog_manager:
        try:
            await dialog_manager.start(CabinetSG.MAIN, mode=StartMode.RESET_STACK)
        except Exception:
            pass
