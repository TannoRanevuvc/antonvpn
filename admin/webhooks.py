"""Robokassa payment result webhook."""
from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

from config import logger

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

_bg_factory = None
_bot = None


def set_bg_factory(factory, bot) -> None:
    global _bg_factory, _bot
    _bg_factory = factory
    _bot = bot


@router.post("/robokassa/result")
async def robokassa_result(request: Request):
    """
    Robokassa calls this URL after successful payment.
    Must return 'OK{InvId}' on success.
    """
    try:
        form = await request.form()
        # Robokassa sends both GET and POST — handle both
        params = dict(form)
        if not params:
            params = dict(request.query_params)

        out_sum = str(params.get("OutSum") or params.get("outsum", "0"))
        inv_id = str(params.get("InvId") or params.get("invid", "0"))
        signature = str(params.get("SignatureValue") or params.get("signaturevalue", ""))

        from database.confdb import async_session_factory
        async with async_session_factory() as session:
            from services.payment_service import PaymentService
            svc = PaymentService(session)
            topup = await svc.finalize_topup(out_sum, inv_id, signature)

            if topup and _bg_factory and _bot:
                # Notify user via bot
                from database.repositories import UserRepository
                repo = UserRepository(session)
                if topup.user_id:
                    user = await repo.get_by_id(topup.user_id)
                    if user:
                        from aiogram_dialog import StartMode
                        from bot.states import PaymentsSG
                        try:
                            bg = _bg_factory.bg(_bot, user.telegram_id, user.chat_id)
                            await bg.start(PaymentsSG.SUCCESS, mode=StartMode.RESET_STACK)
                        except Exception as exc:
                            logger.warning("Could not notify user %s about topup: %s", user.telegram_id, exc)

        return PlainTextResponse(f"OK{inv_id}")
    except Exception as exc:
        logger.error("Robokassa webhook error: %s", exc, exc_info=True)
        return PlainTextResponse("error", status_code=500)


@router.get("/robokassa/result")
async def robokassa_result_get(request: Request):
    """Robokassa also sends GET for Success/Fail URLs."""
    params = dict(request.query_params)
    out_sum = str(params.get("OutSum", "0"))
    inv_id = str(params.get("InvId", "0"))
    signature = str(params.get("SignatureValue", ""))

    try:
        from database.confdb import async_session_factory
        async with async_session_factory() as session:
            from services.payment_service import PaymentService
            svc = PaymentService(session)
            await svc.finalize_topup(out_sum, inv_id, signature)
    except Exception as exc:
        logger.warning("Robokassa GET webhook error: %s", exc)

    return PlainTextResponse(f"OK{inv_id}")
