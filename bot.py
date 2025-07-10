import asyncio
import logging
import os

from aiogram import Dispatcher
from aiogram.client.bot import Bot, DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from tasks.schedule_training_reminders import generate_daily_reminders, send_training_reminders

from handlers.registration import register_handlers
from handlers.subscription import router as subscription_router
from handlers.promo import router as promo_router
from handlers.payment import router as payment_router
from handlers.exercise import router as exercise_router
from handlers.chat import router as chat_router
from handlers.premium import router as premium_router
from handlers.workout import router as workout_router
from handlers.training_reminder import router as training_reminder_router


BOT_TOKEN = os.getenv("BOT_TOKEN")
REDIS_URL = os.getenv("REDIS_URL")

logging.basicConfig(level=logging.INFO)

async def main():
    # Инициализируем бота с дефолтными свойствами (вместо parse_mode)
    default_props = DefaultBotProperties(parse_mode="HTML")
    bot = Bot(token=BOT_TOKEN, default=default_props)

    # in-memory FSM, позже можно заменить на RedisStorage
    storage = RedisStorage.from_url(REDIS_URL)
    dp = Dispatcher(storage=storage)

    # Регистрируем хендлеры
    register_handlers(dp)
    dp.include_router(subscription_router)
    dp.include_router(promo_router)
    dp.include_router(payment_router)
    dp.include_router(exercise_router)
    dp.include_router(chat_router)
    dp.include_router(premium_router)
    dp.include_router(workout_router)
    dp.include_router(training_reminder_router)

    # Запускаем polling
    scheduler = AsyncIOScheduler()
    scheduler.add_job(generate_daily_reminders, "interval", minutes=1)
    scheduler.add_job(send_training_reminders, "interval", minutes=1)
    scheduler.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
