from aiogram.types import ReplyKeyboardMarkup
from keyboards.menu import default_menu, premium_menu
from services.subscription_service import SubscriptionService

class MenuService:
    def __init__(self, telegram_id: int):
        self._sub_svc = SubscriptionService(telegram_id)

    def get_main_menu_markup(self) -> ReplyKeyboardMarkup:
        if self._sub_svc.has_active():
            return premium_menu()
        return default_menu()
