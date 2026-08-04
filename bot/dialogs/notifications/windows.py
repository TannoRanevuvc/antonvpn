from aiogram_dialog import Window
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Format

from bot.states import CabinetSG, NotifySG


def _build_notify_window(state, text_key: str):
    async def getter(dialog_manager, **kwargs):
        session = dialog_manager.middleware_data.get("session")
        from bot.utils.message_builder import build_payload_by_key
        payload = await build_payload_by_key(text_key, session)
        return {"text": payload["text"], "image_path": payload["image_path"]}

    from aiogram_dialog.widgets.media import DynamicMedia
    return Window(
        DynamicMedia("image_path", when="image_path"),
        Format("{text}"),
        Button(Format("💳 Продлить"), id="renew", on_click=lambda c, b, m: m.start(CabinetSG.MAIN)),
        state=state,
        getter=getter,
        parse_mode="HTML",
    )


def build_notification_windows() -> list[Window]:
    return [
        _build_notify_window(NotifySG.EXPIRY_3D, "EXPIRY_3D"),
        _build_notify_window(NotifySG.EXPIRY_1D, "EXPIRY_1D"),
        _build_notify_window(NotifySG.EXPIRY_1H, "EXPIRY_1H"),
        _build_notify_window(NotifySG.EXPIRED, "EXPIRED"),
    ]
