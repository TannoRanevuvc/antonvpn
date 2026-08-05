"""Seed initial data into the database."""
import asyncio

from sqlalchemy import select

from database.confdb import async_session_factory
from database.models import (
    BotSettings,
    ChannelSettings,
    MessageTemplate,
    NotificationRule,
    ReferralSettings,
    Tariff,
)
from database.models.subscription import TariffType
from config import logger

MESSAGE_TEMPLATES = [
    ("CABINET", (
        "👤 <b>Личный кабинет</b>\n\n"
        "Имя: {first_name}\n"
        "Telegram ID: <code>{telegram_id}</code>\n"
        "Баланс: <b>{balance}₽</b>\n"
        "Подписок: {sub_count}"
    )),
    ("SUB_LIST", "📱 <b>Ваши подписки</b>\n\nВыберите подписку для управления:"),
    ("SUB_DETAIL", (
        "🔑 <b>{name}</b>\n\n"
        "Тип: {tariff_type}\n"
        "Истекает: {expires_at}\n"
        "Устройства: {device_count}/{max_devices}\n"
        "Автопродление: {auto_renewal}\n\n"
        "Ссылка подписки:\n<code>{sub_url}</code>"
    )),
    ("TOPUP_AMOUNT", "💳 Пополнение баланса\n\nВаш баланс: <b>{balance}₽</b>\n\nВведите сумму пополнения (минимум 100₽):"),
    ("TOPUP_SUCCESS", "✅ Баланс успешно пополнен!"),
    ("GIFT_SENT", "🎁 Подарок создан!\n\nСсылка для получателя:\n<code>{gift_link}</code>\n\nОтправьте её другу."),
    ("GIFT_ACTIVATE", "🎁 Вам подарили подписку!\n\nТариф: <b>{tariff_name}</b>\n\nАктивировать?"),
    ("GIFT_SUCCESS", "✅ Подарок активирован! Подписка добавлена в ваш список."),
    ("REF_INFO", (
        "👥 <b>Реферальная программа</b>\n\n"
        "Ваша ссылка:\n<code>{ref_link}</code>\n\n"
        "Приглашено: <b>{ref_count}</b> чел.\n\n"
        "За каждого приглашённого друга вы получаете бонус!"
    )),
    ("EXPIRY_3D", "⚠️ Ваша подписка <b>{sub_name}</b> истекает через <b>3 дня</b>.\n\nПродлите подписку, чтобы не потерять доступ!"),
    ("EXPIRY_1D", "🔶 Ваша подписка <b>{sub_name}</b> истекает <b>завтра</b>!\n\nНе забудьте продлить доступ."),
    ("EXPIRY_1H", "🔴 Ваша подписка <b>{sub_name}</b> истекает через <b>1 час</b>!\n\nСрочно продлите подписку."),
    ("EXPIRED", "❌ Ваша подписка истекла.\n\nОформите новую подписку в личном кабинете."),
    ("CHANNEL_GATE", "📢 Для использования бота необходимо подписаться на наш канал.\n\nПосле подписки нажмите кнопку «Проверить»."),
    ("TARIFF_TYPE_SELECT", "🔌 Выберите тип подписки:"),
    ("TARIFF_CONFIRM", (
        "<b>{tariff_title}</b>\n"
        "Срок: {duration_days} дней\n"
        "Стоимость: {price_rub}₽\n\n"
        "Баланс: {balance}₽\n"
        "После оплаты: {balance_after}₽"
    )),
    ("OFERTA", (
        "📄 <b>Оферта</b>\n\n"
        "Пользуясь ботом, вы соглашаетесь с условиями предоставления услуг.\n\n"
        "Отредактируйте этот текст в разделе «Шаблоны сообщений» в административной панели."
    )),
]

NOTIFICATION_RULES = [
    ("За 3 дня", 72, "EXPIRY_3D"),
    ("За 1 день", 24, "EXPIRY_1D"),
    ("За 1 час", 1, "EXPIRY_1H"),
]

EXAMPLE_TARIFFS = [
    ("VPN — 1 месяц", TariffType.VPN, 30, 299.0, 1, 0),
    ("VPN — 3 месяца", TariffType.VPN, 90, 799.0, 1, 1),
    ("VPN — 6 месяцев", TariffType.VPN, 180, 1399.0, 2, 2),
    ("Обход глушилок — 1 месяц", TariffType.OBFUSCATED, 30, 399.0, 1, 3),
    ("Обход глушилок — 3 месяца", TariffType.OBFUSCATED, 90, 999.0, 2, 4),
]


async def seed() -> None:
    async with async_session_factory() as session:
        # Message templates
        for key, text in MESSAGE_TEMPLATES:
            existing = await session.execute(select(MessageTemplate).where(MessageTemplate.key == key))
            if not existing.scalar_one_or_none():
                session.add(MessageTemplate(key=key, text=text))

        # Notification rules
        for label, hours, template_key in NOTIFICATION_RULES:
            existing = await session.execute(
                select(NotificationRule).where(NotificationRule.hours_before_expiry == hours)
            )
            if not existing.scalar_one_or_none():
                session.add(NotificationRule(label=label, hours_before_expiry=hours, message_template_key=template_key))

        # Singleton settings
        if not (await session.execute(select(BotSettings).where(BotSettings.id == 1))).scalar_one_or_none():
            session.add(BotSettings(id=1))

        if not (await session.execute(select(ReferralSettings).where(ReferralSettings.id == 1))).scalar_one_or_none():
            session.add(ReferralSettings(id=1))

        if not (await session.execute(select(ChannelSettings).where(ChannelSettings.id == 1))).scalar_one_or_none():
            session.add(ChannelSettings(id=1))

        # Example tariffs (only if none exist)
        existing_count = (await session.execute(select(Tariff))).scalars().all()
        if not existing_count:
            for title, tariff_type, duration_days, price_rub, max_devices, sort_order in EXAMPLE_TARIFFS:
                session.add(Tariff(
                    title=title,
                    tariff_type=tariff_type,
                    duration_days=duration_days,
                    price_rub=price_rub,
                    max_devices=max_devices,
                    sort_order=sort_order,
                ))

        await session.commit()
        logger.info("Database seeded successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
