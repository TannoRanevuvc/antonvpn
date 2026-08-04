from aiogram_dialog import DialogManager


async def topup_amount_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    user = dialog_manager.middleware_data.get("user")
    return {
        "balance": f"{float(user.balance_rub):.2f}",
        "text": f"💳 Ваш баланс: <b>{float(user.balance_rub):.2f}₽</b>\n\nВведите сумму пополнения (минимум 100₽):",
    }


async def topup_confirm_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    amount = dialog_manager.dialog_data.get("amount", 0)
    return {
        "text": f"Вы собираетесь пополнить баланс на <b>{amount:.2f}₽</b>.\nНажмите кнопку ниже для оплаты через Robokassa.",
        "amount": amount,
        "payment_url": dialog_manager.dialog_data.get("payment_url", ""),
    }


async def topup_success_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    return {"text": "✅ Баланс успешно пополнен!"}
