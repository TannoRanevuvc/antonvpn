from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RemnawaveUser(BaseModel):
    uuid: str
    username: str
    short_uuid: str | None = Field(None, alias="shortUuid")
    subscription_url: str | None = Field(None, alias="subscriptionUrl")
    status: str = "ACTIVE"
    expire_at: datetime | None = Field(None, alias="expireAt")
    traffic_limit_bytes: int | None = Field(None, alias="trafficLimitBytes")

    model_config = {"populate_by_name": True}


class RemnawaveDevice(BaseModel):
    id: str
    model: str | None = None
    os: str | None = None
    os_version: str | None = Field(None, alias="osVersion")
    client_version: str | None = Field(None, alias="clientVersion")
    last_seen: datetime | None = Field(None, alias="lastSeen")

    model_config = {"populate_by_name": True}
