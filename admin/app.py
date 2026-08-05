from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqladmin import Admin
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.sessions import SessionMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from admin.auth import AdminAuthBackend
from admin.views.basic import (
    ChannelSettingsAdmin,
    DeviceAdmin,
    GiftAdmin,
    LegalDocumentAdmin,
    MessageTemplateAdmin,
    NotificationRuleAdmin,
    PaymentAdmin,
    ReferralAdmin,
    ReferralSettingsAdmin,
    BotSettingsAdmin,
    SubscriptionAdmin,
    TariffAdmin,
    TopUpAdmin,
    UserAdmin,
)
from admin.views.custom import BroadcastView, DashboardView
from admin.documents import router as documents_router
from admin.subscription_page import router as sub_page_router
from admin.webhooks import router as webhooks_router
from config import settings
from database.confdb import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="AntonVPN Admin",
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
    )

    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")
    app.add_middleware(SessionMiddleware, secret_key=settings.JWT_SECRET_KEY)

    # Admin panel
    auth_backend = AdminAuthBackend(secret_key=settings.JWT_SECRET_KEY)
    admin = Admin(
        app,
        engine=engine,
        authentication_backend=auth_backend,
        base_url=settings.BASE_ADMIN_URL,
        title="AntonVPN Admin",
    )

    # Register model views
    for view_cls in [
        UserAdmin, ReferralAdmin,
        SubscriptionAdmin, DeviceAdmin,
        TariffAdmin,
        TopUpAdmin, PaymentAdmin,
        GiftAdmin,
        MessageTemplateAdmin,
        NotificationRuleAdmin,
        BotSettingsAdmin, ReferralSettingsAdmin, ChannelSettingsAdmin,
        LegalDocumentAdmin,
    ]:
        admin.add_view(view_cls)

    # Custom views
    admin.add_view(DashboardView)
    admin.add_view(BroadcastView)

    # Routers
    app.include_router(documents_router)
    app.include_router(sub_page_router)
    app.include_router(webhooks_router)

    # Serve React SPA static assets
    webapp_dist = Path(__file__).parent.parent / "webapp" / "dist" / "static"
    if webapp_dist.exists():
        app.mount("/assets/static", StaticFiles(directory=str(webapp_dist)), name="spa-assets")

    return app


app = create_app()
