from aiogram_dialog import DialogManager

from bot.utils.deep_link import gift_link
from services.tariff_service import TariffService


async def gift_tariff_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    session = dialog_manager.middleware_data.get("session")
    user = dialog_manager.middleware_data.get("user")
    svc = TariffService(session)
    tariffs = await svc.list_active()
    items = [(f"🎁 {t.title} — {t.price_rub}₽", str(t.id)) for t in tariffs]
    return {
        "text": f"Выберите тариф для подарка.\nВаш баланс: <b>{float(user.balance_rub):.2f}₽</b>",
        "tariff_items": items,
        "has_tariffs": bool(items),
    }


async def gift_confirm_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    session = dialog_manager.middleware_data.get("session")
    user = dialog_manager.middleware_data.get("user")
    tariff_id = dialog_manager.dialog_data.get("tariff_id")

    svc = TariffService(session)
    tariff = await svc.get_by_id(int(tariff_id))
    if not tariff:
        return {"text": "Тариф недоступен.", "can_buy": False}

    balance = float(user.balance_rub)
    price = float(tariff.price_rub)
    can_buy = balance >= price

    return {
        "text": (
            f"🎁 Вы дарите: <b>{tariff.title}</b> ({tariff.duration_days}д)\n"
            f"Стоимость: {price:.2f}₽\nВаш баланс: {balance:.2f}₽"
        ),
        "can_buy": can_buy,
    }


async def gift_sent_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    code = dialog_manager.dialog_data.get("gift_code", "")
    link = gift_link(code) if code else ""
    return {
        "text": f"✅ Подарок создан!\n\nСсылка для получателя:\n<code>{link}</code>\n\nОтправьте её другу.",
        "gift_link": link,
    }


async def gift_activate_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    session = dialog_manager.middleware_data.get("session")
    code = dialog_manager.dialog_data.get("gift_code", "")
    from database.repositories import GiftRepository, TariffRepository
    gift = await GiftRepository(session).get_by_code(code)
    if not gift:
        return {"text": "Подарок не найден или устарел.", "can_activate": False}

    tariff = await TariffRepository(session).get_by_id_active(gift.tariff_id)
    name = tariff.title if tariff else "подписку"
    return {
        "text": f"🎁 Вам подарили: <b>{name}</b>\nАктивировать?",
        "can_activate": True,
        "gift_code": code,
    }


async def gift_success_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    return {"text": "✅ Подарок активирован! Подписка добавлена в ваш список."}
