import os
import asyncio
import logging
from datetime import date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone
from services.gpt_reminder_service import GptReminderService
from services.reminder_text_service import ReminderTextService
from services.training_reminder_service import TrainingReminderService
from aiogram import Bot
from aiogram.fsm.storage.redis import RedisStorage

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
REDIS_URL = os.getenv("REDIS_URL")

bot = Bot(token=BOT_TOKEN)
gpt_service = GptReminderService()
reminder_text_service = ReminderTextService(gpt_service)
storage = RedisStorage.from_url(REDIS_URL)
training_reminder_service = TrainingReminderService(bot, reminder_text_service, storage)

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

async def generate_daily_reminders():
    today = date.today()
    await reminder_text_service.generate_for_both(today)
    logging.info(f"[Reminders] Напоминалки на {today} успешно сгенерированы.")

async def send_training_reminders():
    await training_reminder_service.send_today_reminders()
    logging.info(f"[Reminders] Проверка и рассылка напоминаний завершена.")

def start_scheduler():
    scheduler.add_job(generate_daily_reminders, "interval", minutes=1440, id="generate_daily_reminders")
    scheduler.add_job(send_training_reminders, "interval", minutes=60, id="send_training_reminders")
    scheduler.start()
    logging.info("[Scheduler] Планировщик задач стартовал.")

async def main():
    start_scheduler()
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
