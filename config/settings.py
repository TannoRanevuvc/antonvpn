from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="config/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://antonvpn_user:antonvpn_pass@postgres:5432/antonvpn"
    REDIS_URL: str = "redis://redis:6379/0"

    # Telegram bot
    TOKEN_BOT_TG: str
    BOT_LINK: str = ""

    # Remnawave VPN panel
    REMNAWAVE_PANEL_URL: str
    REMNAWAVE_TOKEN: str

    # Robokassa
    SHOP_IND: str = ""
    PASS1: str = ""
    PASS2: str = ""
    ROBOKASSA_IS_TEST: bool = False

    # Admin panel
    ADMIN_USER: str = "admin"
    ADMIN_PASSWORD: str = "admin"
    BASE_ADMIN_URL: str = "/admin"
    ADMIN_PUBLIC_BASE_URL: str = "http://localhost:8000"
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"

    # Channel gate (optional, can be set in DB via ChannelSettings)
    CHANNEL_ID: int = 0

    # Proxy (optional)
    SOCKS5_PROXY_URL: str = ""

    # Media
    MEDIA_DIR: str = "media"


settings = Settings()
