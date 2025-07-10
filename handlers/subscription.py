from aiogram import Router, F
from aiogram.types import CallbackQuery
from services.subscription_service import SubscriptionService

router = Router(name="subscription")


@router.callback_query(F.data == "tariff_trial")
async def handle_trial(callback: CallbackQuery):
    svc = SubscriptionService(callback.from_user.id)
    try:
        end_dt = svc.trial()
    except ValueError as e:
        await callback.answer(str(e), show_alert=True)
        return
    finally:
        svc.close()

    end_str = end_dt.strftime("%d.%m %H:%M")
    await callback.message.answer(
        f"🎉 Ваша пробная подписка активирована до *{end_str}*\n\n"
        "Пока у вас действует пробная неделя, вы можете:\n"
        "• Пользоваться полной библиотекой упражнений\n"
        "• Задавать любые вопросы в чате\n\n"
        "Приятных тренировок! 💪",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "tariff_stay_free")
async def handle_stay_free(callback: CallbackQuery):
    """
    Обработчик кнопки «Остаться в бесплатном тарифе»
    — просто показывает Alert и ничего более не делает.
    """
    await callback.message.answer(
        "👍 Вы остаетесь на бесплатном тарифе!"
    )
    await callback.answer()
