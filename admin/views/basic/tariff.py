from sqladmin import ModelView

from database.models.tariff import Tariff


class TariffAdmin(ModelView, model=Tariff):
    name = "Тариф"
    name_plural = "Тарифы"
    icon = "fa-solid fa-tags"
    column_list = [Tariff.id, Tariff.title, Tariff.tariff_type, Tariff.duration_days, Tariff.price_rub, Tariff.max_devices, Tariff.is_active, Tariff.sort_order]
    column_sortable_list = [Tariff.sort_order, Tariff.price_rub]
    form_columns = [Tariff.title, Tariff.tariff_type, Tariff.duration_days, Tariff.price_rub, Tariff.max_devices, Tariff.squad_uuid, Tariff.is_active, Tariff.sort_order]

    async def after_model_change(self, data, model, is_created, request) -> None:
        from database.cache import TariffCache
        await TariffCache.delete()
