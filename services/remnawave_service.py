"""Thin service wrapper over the Remnawave API client."""
from datetime import datetime

from integrations.remnawave import client as remna
from integrations.remnawave.exceptions import RemnawaveApiError
from config import logger


class RemnawaveService:
    async def create_user(
        self,
        username: str,
        expires_at: datetime | None,
        squad_uuid: str | None = None,
    ) -> dict:
        squads = [squad_uuid] if squad_uuid else []
        data = await remna.create_user(
            username=username,
            expires_at=expires_at,
            status="ACTIVE" if expires_at and expires_at > datetime.utcnow() else "DISABLED",
            active_internal_squad_uuids=squads,
        )
        return data

    async def update_user(
        self,
        remna_uuid: str,
        status: str | None = None,
        expires_at: datetime | None = None,
        squad_uuid: str | None = None,
    ) -> dict:
        squads = [squad_uuid] if squad_uuid else None
        return await remna.update_user(
            user_uuid=remna_uuid,
            status=status,
            expires_at=expires_at,
            active_internal_squad_uuids=squads,
        )

    async def disable_user(self, remna_uuid: str) -> bool:
        try:
            await remna.update_user(user_uuid=remna_uuid, status="DISABLED")
            return True
        except RemnawaveApiError as exc:
            logger.warning("Failed to disable remnawave user %s: %s", remna_uuid, exc)
            return False

    async def list_devices(self, remna_uuid: str) -> list[dict]:
        try:
            return await remna.list_user_devices(remna_uuid)
        except RemnawaveApiError as exc:
            logger.warning("Failed to list devices for %s: %s", remna_uuid, exc)
            return []

    async def delete_device(self, remna_uuid: str, device_id: str) -> bool:
        try:
            await remna.delete_device(remna_uuid, device_id)
            return True
        except RemnawaveApiError as exc:
            logger.warning("Failed to delete device %s for user %s: %s", device_id, remna_uuid, exc)
            return False
