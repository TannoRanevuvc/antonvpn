from aiogram_dialog import DialogManager

from database.models.subscription import TariffType
from services.tariff_service import TariffService


async def tariff_type_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    return {"text": "Выберите тип подписки:"}


async def tariff_list_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    session = dialog_manager.middleware_data.get("session")
    selected_type = dialog_manager.dialog_data.get("tariff_type", TariffType.VPN.value)

    svc = TariffService(session)
    tariffs = await svc.list_by_type(TariffType(selected_type))

    items = [
        (f"{t.title} — {t.price_rub}₽ / {t.duration_days}д", str(t.id))
        for t in tariffs
    ]

    return {
        "text": "Выберите тариф:",
        "tariff_items": items,
        "has_tariffs": bool(items),
    }


async def tariff_confirm_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    session = dialog_manager.middleware_data.get("session")
    user = dialog_manager.middleware_data.get("user")
    tariff_id = dialog_manager.dialog_data.get("tariff_id")

    if not tariff_id:
        return {"text": "Тариф не выбран.", "can_buy": False}

    svc = TariffService(session)
    tariff = await svc.get_by_id(int(tariff_id))

    if not tariff:
        return {"text": "Тариф недоступен.", "can_buy": False}

    balance = float(user.balance_rub)
    price = float(tariff.price_rub)
    after = balance - price
    can_buy = balance >= price

    text = (
        f"<b>{tariff.title}</b>\n"
        f"Срок: {tariff.duration_days} дней\n"
        f"Стоимость: {price:.2f}₽\n\n"
        f"Баланс: {balance:.2f}₽\n"
        f"После оплаты: {after:.2f}₽"
    )

    if not can_buy:
        text += "\n\n❌ Недостаточно средств. Пополните баланс."

    return {"text": text, "can_buy": can_buy}
