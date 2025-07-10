import os
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from services.subscription_reminder_service import SubscriptionReminderService

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Инициализация бота и сервиса
bot = Bot(token=BOT_TOKEN)
reminder_service = SubscriptionReminderService(bot)

async def send_due_subscription_reminders():
    """
    Проверяет и рассылает напоминания об окончании подписки (по remind_at из БД).
    """
    await reminder_service.send_due_reminders()
    logging.info("[Subscription Reminders] Проверка и рассылка напоминаний завершена.")

def start_scheduler():
    scheduler = AsyncIOScheduler()
    # Проверяем каждый 1–5 минут, чтобы не пропустить нужную дату/время
    scheduler.add_job(send_due_subscription_reminders, "interval", minutes=1)
    scheduler.start()
    logging.info("[Subscription Reminders] Планировщик задач стартовал.")

async def main():
    start_scheduler()
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
