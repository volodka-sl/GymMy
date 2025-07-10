from decimal import Decimal
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from states import PromoStates
from services.promo_service import PromoService, PromoResult
from services.payment_service import PaymentService

from services.main_menu_service import MenuService
from services.subscription_service import SubscriptionService

router = Router(name="promo")


@router.callback_query(F.data == "tariff_promo")
async def prompt_promo(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PromoStates.enter_code)
    await callback.message.answer("🔑 Пожалуйста, введите ваш промокод:")
    await callback.answer()


@router.message(PromoStates.enter_code)
async def process_promo(message: Message, state: FSMContext):
    code = message.text.strip()
    svc  = PromoService(message.from_user.id)

    try:
        # Передаем в сервис стоимость подписки 990₽, чтобы он мог её пересчитать
        result: PromoResult = svc.apply_code(code, original_amount=Decimal('990.00'))
    except ValueError as e:
        await message.answer(f"❗️ {e}")
        svc.close()
        return

    svc.close()
    menu_service = MenuService(SubscriptionService(message.from_user.id))

    # 1) Если free_days — как было
    if result.type == 'free_days':
        end_str, desc = result.value, result.description
        await message.answer(
            f"🎉 Промокод *{code}* успешно применён!\n"
            f"{desc}\n\n"
            f"Ваша подписка продлена до *{end_str}* по вашему часовому поясу.",
            parse_mode="Markdown",
            reply_markup=MenuService(message.from_user.id).get_main_menu_markup()
        )

    # 2) Если скидка — формируем ссылку на оплату по новой цене
    else:
        new_price: Decimal = result.value  # Decimal
        desc = result.description
        pay_svc = PaymentService(message.from_user.id)
        try:
            link = await pay_svc.generate_payment_link(amount=new_price)
        finally:
            pay_svc.close()

        await message.answer(
            (
                f"🎉 Промокод *{code}* успешно применён!\n"
                f"Описание промокода: {desc}\n\n"
                f"Новая цена подписки: <b>{new_price:.2f}₽</b>.\n"
                f"Чтобы оплатить, перейди по "
                f"<a href=\"{link}\"><b>ссылке</b></a>"
            ),
            parse_mode="HTML",
            reply_markup=MenuService(message.from_user.id).get_main_menu_markup()
        )

    await state.clear()
