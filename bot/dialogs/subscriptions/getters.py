from datetime import datetime

from aiogram_dialog import DialogManager

from bot.utils.message_builder import build_payload_by_key
from database.repositories import SubscriptionRepository
from services.subscription_service import SubscriptionService


async def subscriptions_list_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    session = dialog_manager.middleware_data.get("session")
    user = dialog_manager.middleware_data.get("user")
    repo = SubscriptionRepository(session)
    subs = await repo.get_by_user_id(user.id)

    payload = await build_payload_by_key("SUB_LIST", session)

    items = []
    for sub in subs:
        name = sub.display_name or sub.remna_username
        exp = sub.expires_at.strftime("%d.%m.%Y") if sub.expires_at else "—"
        status = "✅" if sub.remna_status.value == "ACTIVE" else "❌"
        items.append((f"{status} {name} | до {exp}", str(sub.id)))

    return {
        "text": payload["text"],
        "image_path": payload["image_path"],
        "subscriptions": items,
        "has_subscriptions": bool(items),
    }


async def subscription_detail_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    session = dialog_manager.middleware_data.get("session")
    user = dialog_manager.middleware_data.get("user")
    sub_id = dialog_manager.dialog_data.get("sub_id")
    if not sub_id:
        return {"text": "Подписка не выбрана.", "image_path": None}

    repo = SubscriptionRepository(session)
    sub = await repo.get_by_id_and_user(int(sub_id), user.id)
    if not sub:
        return {"text": "Подписка не найдена.", "image_path": None}

    payload = await build_payload_by_key("SUB_DETAIL", session)
    name = sub.display_name or sub.remna_username
    exp = sub.expires_at.strftime("%d.%m.%Y %H:%M") if sub.expires_at else "—"
    device_count = len(sub.devices)
    auto = "✅ Вкл" if sub.auto_renewal else "❌ Выкл"
    sub_url = sub.remna_sub_url or "—"

    text = payload["text"].format(
        name=name,
        sub_url=sub_url,
        tariff_type=sub.tariff_type.value,
        expires_at=exp,
        device_count=device_count,
        max_devices=sub.max_devices,
        auto_renewal=auto,
    )

    return {
        "text": text,
        "image_path": payload["image_path"],
        "sub_id": sub_id,
        "sub_url": sub_url,
        "auto_renewal": sub.auto_renewal,
        "sub_active": sub.remna_status.value == "ACTIVE",
    }


async def devices_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    session = dialog_manager.middleware_data.get("session")
    user = dialog_manager.middleware_data.get("user")
    sub_id = dialog_manager.dialog_data.get("sub_id")

    repo = SubscriptionRepository(session)
    sub = await repo.get_by_id_and_user(int(sub_id), user.id)

    svc = SubscriptionService(session)
    devices = await svc.sync_devices_from_panel(sub)

    lines = []
    for i, d in enumerate(devices, 1):
        model = d.model or "Неизвестно"
        os_str = f"{d.os or ''} {d.os_version or ''}".strip() or "—"
        last = d.last_seen.strftime("%d.%m %H:%M") if d.last_seen else "—"
        lines.append(f"{i}. {model} | {os_str} | {last}")

    device_items = [(f"{i+1}. {d.model or d.remna_device_id}", d.remna_device_id) for i, d in enumerate(devices)]

    return {
        "text": "\n".join(lines) if lines else "Устройства не найдены.",
        "image_path": None,
        "device_items": device_items,
        "device_count": len(devices),
        "max_devices": sub.max_devices,
    }
