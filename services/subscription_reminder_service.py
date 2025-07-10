# services/subscription_reminder_service.py

from datetime import datetime, timezone
from storage.subscription_reminder_repository import SubscriptionReminderRepository
from storage.subscription_repository import SubscriptionRepository
from storage.user_repository import UserRepository
from aiogram import Bot
from services.main_menu_service import MenuService

class SubscriptionReminderService:
    """
    Сервис для рассылки напоминаний об оплате подписки.
    """

    def __init__(self, bot: Bot):
        self._bot = bot
        self._reminder_repo = SubscriptionReminderRepository()
        self._user_repo = UserRepository()
        self._subscription_repo = SubscriptionRepository()

    async def send_due_reminders(self):
        now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
        reminders = self._reminder_repo.list_unsent_reminders(now_utc)
        for reminder in reminders:
            # Получаем подписку и пользователя
            subscription = self._subscription_repo.get_by_id(reminder.user_subscription_id)
            if not subscription:
                continue
            user = self._user_repo.get_by_id(subscription.user_id)
            if not user:
                continue

            # Генерируем текст и меню
            markup = None
            if reminder.type == "before_3d":
                text = (
                    "⚠️ Ваша Premium-подписка заканчивается через 3 дня.\n"
                    "Чтобы не потерять доступ к тренировкам и чату с Gymmy, продлите подписку вовремя!"
                )
            elif reminder.type == "on_end":
                text = (
                    "❗️ Ваша Premium-подписка закончилась.\n"
                    "Для продолжения пользования премиум-функциями Gymmy, пожалуйста, оформите новую подписку."
                )
                # Меню переключаем на дефолтное
                markup = MenuService(user.telegram_id).get_main_menu_markup()
            else:
                text = "Напоминание о подписке."
                markup = None

            # Пытаемся отправить уведомление
            try:
                await self._bot.send_message(
                    chat_id=user.telegram_id,
                    text=text,
                    reply_markup=markup
                )
                self._reminder_repo.mark_as_sent(reminder)
            except Exception as e:
                print(f"Не удалось отправить напоминание user_id={user.user_id}: {e}")

        self._reminder_repo.close()
