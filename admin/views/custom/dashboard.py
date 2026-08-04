"""Admin dashboard with aggregate statistics, Redis-cached."""
from datetime import datetime, timedelta

from sqladmin import BaseView, expose
from starlette.requests import Request

from database.cache import DashboardCache
from database.confdb import async_session_factory


async def _build_stats() -> dict:
    from sqlalchemy import func, select
    from database.models.user import User
    from database.models.subscription import Subscription, RemnaStatus, TariffType
    from database.models.payment import TopUp, TopUpStatus, Payment, PaymentStatus

    async with async_session_factory() as session:
        now = datetime.utcnow()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        total_users = (await session.execute(select(func.count(User.id)))).scalar_one()
        users_today = (await session.execute(select(func.count(User.id)).where(User.created_at >= today))).scalar_one()
        users_7d = (await session.execute(select(func.count(User.id)).where(User.created_at >= week_ago))).scalar_one()

        active_subs = (await session.execute(
            select(func.count(Subscription.id)).where(Subscription.remna_status == RemnaStatus.ACTIVE)
        )).scalar_one()
        active_vpn = (await session.execute(
            select(func.count(Subscription.id)).where(
                Subscription.remna_status == RemnaStatus.ACTIVE,
                Subscription.tariff_type == TariffType.VPN,
            )
        )).scalar_one()
        active_obfs = (await session.execute(
            select(func.count(Subscription.id)).where(
                Subscription.remna_status == RemnaStatus.ACTIVE,
                Subscription.tariff_type == TariffType.OBFUSCATED,
            )
        )).scalar_one()

        expiring_3d = (await session.execute(
            select(func.count(Subscription.id)).where(
                Subscription.expires_at.between(now, now + timedelta(days=3)),
                Subscription.remna_status == RemnaStatus.ACTIVE,
            )
        )).scalar_one()
        expiring_7d = (await session.execute(
            select(func.count(Subscription.id)).where(
                Subscription.expires_at.between(now, now + timedelta(days=7)),
                Subscription.remna_status == RemnaStatus.ACTIVE,
            )
        )).scalar_one()

        revenue_today = (await session.execute(
            select(func.coalesce(func.sum(TopUp.amount_rub), 0)).where(
                TopUp.status == TopUpStatus.PAID,
                TopUp.paid_at >= today,
            )
        )).scalar_one()
        revenue_30d = (await session.execute(
            select(func.coalesce(func.sum(TopUp.amount_rub), 0)).where(
                TopUp.status == TopUpStatus.PAID,
                TopUp.paid_at >= month_ago,
            )
        )).scalar_one()
        topup_count = (await session.execute(
            select(func.count(TopUp.id)).where(TopUp.status == TopUpStatus.PAID)
        )).scalar_one()

        return {
            "total_users": total_users,
            "users_today": users_today,
            "users_7d": users_7d,
            "active_subs": active_subs,
            "active_vpn": active_vpn,
            "active_obfs": active_obfs,
            "expiring_3d": expiring_3d,
            "expiring_7d": expiring_7d,
            "revenue_today": float(revenue_today),
            "revenue_30d": float(revenue_30d),
            "topup_count": topup_count,
            "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        }


class DashboardView(BaseView):
    name = "Дашборд"
    icon = "fa-solid fa-chart-line"

    @expose("/admin/dashboard", methods=["GET"])
    async def dashboard(self, request: Request):
        cached = await DashboardCache.get()
        if cached:
            stats = cached
        else:
            stats = await _build_stats()
            await DashboardCache.set(stats)
        return await self.templates.TemplateResponse(
            request,
            "sqladmin/dashboard.html",
            {"stats": stats},
        )
