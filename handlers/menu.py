from aiogram import types, Dispatcher, F
from aiogram.fsm.context import FSMContext

import keyboards.menu as menu_kb
from handlers.configs.registration_config import FIELD_CONFIG, CONFIG_BY_KEY
from handlers.registration import _ask_field
from services.user_service import UserService


async def update_data(message: types.Message, state: FSMContext):
    """
    Обработчик кнопки «Обновить данные» из главного меню.
    Сброс FSM и запуск воронки заново.
    """
    svc = UserService(message.from_user.id)
    if not svc.exists():
        await message.answer(
            "Я пока не знаю твоих данных. Сначала заполни профиль командой /start."
        )
        svc.close()
        return
    svc.close()

    # Скрываем текущее меню и запускаем воронку
    await message.answer(
        "Обновим твои данные:",
        reply_markup=types.ReplyKeyboardRemove()
    )

    await state.clear()
    first_key = FIELD_CONFIG[0]['key']
    await _ask_field(message, state, first_key)
    await state.set_state(CONFIG_BY_KEY[first_key]['state'])

def register_menu_handlers(dp: Dispatcher):
    """
    Регистрируем только кнопку «Обновить данные» — она приходит через ReplyKeyboard.
    """
    dp.message.register(
        update_data,
        F.text == "✍️ Обновить данные"
    )
