from aiogram import Router, F
from aiogram.types import Message

from services.subscription_service import SubscriptionService
from keyboards.inline_keyboards import tariffs_kb

router = Router()

TARIFFS_TEXT = (
    "Сейчас ты находишься на бесплатном тарифе.\n\n"
    "📦 *Что в него включено:*\n"
    "• Библиотека упражнений для новичков\n"
    "• Чат с общими рекомендациями по питанию\n\n"
    "🚀 Также у нас есть *Премиум-версия (990 ₽/мес), которая включает в себя:*\n"
    "• Персонализированный план тренировок\n"
    "• Полную библиотеку упражнений\n"
    "• Подробные рекомендации по питанию\n"
    "• Чат с любыми вопросами по питанию, здоровью и спорту\n"
    "• Моральную поддержку и мотивацию 😊\n\n"
    "Попробуем бесплатную неделю или сразу перейдем на Премиум?"
)

@router.message(F.text == "⭐ Premium")
async def premium_info(message: Message):
    svc = SubscriptionService(message.from_user.id)
    try:
        if svc.has_active():
            await message.answer("У вас уже активна подписка 😊")
            return
    finally:
        svc.close()

    await message.answer(
        TARIFFS_TEXT,
        parse_mode="Markdown",
        reply_markup=tariffs_kb()
    )
