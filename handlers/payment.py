from aiogram import Router, F
from aiogram.types import CallbackQuery
from services.subscription_service import SubscriptionService
from services.payment_service import PaymentService

router = Router(name="payment")

@router.callback_query(F.data == "tariff_pay")
async def handle_payment(callback: CallbackQuery):
    tg_id = callback.from_user.id

    # 1) Проверяем, нет ли у пользователя активной подписки
    sub_svc = SubscriptionService(tg_id)
    try:
        if sub_svc.has_active():
            end_dt = sub_svc.current_end()
            # Показываем alert вместо отправки сообщения
            await callback.answer(
                f"❗️ Ваша подписка уже активна до {end_dt.strftime('%d.%m')}. "
                "Продлить сейчас нельзя.",
                show_alert=True
            )
            return
    finally:
        sub_svc.close()

    # 2) Генерируем ссылку на оплату
    try:
        svc = PaymentService(tg_id)
    except ValueError as e:
        # Пользователь не зарегистрирован или профиль не заполнен
        await callback.answer(f"❗️ {e}", show_alert=True)
        return

    try:
        link = await svc.generate_payment_link(amount=990)
    except ValueError as e:
        # Бизнес-ошибка (например, пробный уже был)
        await callback.answer(f"❗️ {e}", show_alert=True)
        return
    except Exception:
        await callback.answer(
            "❗️ Не удалось сформировать платёж. Попробуйте чуть позже.",
            show_alert=True
        )
        return
    finally:
        svc.close()

    # 3) Отправляем пользователю ссылку на оплату в чат
    await callback.message.answer(
        '💳 Чтобы перейти к оплате Premium-версии (990 ₽), перейдите, пожалуйста, по '
        f'<a href="{link}"><b>ссылке</b></a>',
        parse_mode="HTML"
    )
    # подтверждаем коллбек, чтобы UI не висел
    await callback.answer()
