import re
from datetime import date
from inspect import signature

from aiogram import types, Dispatcher, F
from aiogram.filters.command import CommandStart
from aiogram.filters.state import StateFilter
from aiogram.fsm.context import FSMContext

import keyboards.inline_keyboards as keyboards
from services.main_menu_service import MenuService
from handlers.configs.registration_config import FIELD_CONFIG, CONFIG_BY_KEY, STATE_TO_KEY
from states import RegistrationStates
from services.user_service import UserService
from services.subscription_service import SubscriptionService


async def _ask_field(obj: types.Message, state: FSMContext, key: str):
    cfg = CONFIG_BY_KEY[key]
    data = await state.get_data()

    # Подготовка клавиатуры
    kb = None
    kb_name = cfg.get("keyboard")
    if isinstance(kb_name, str):
        kb_func = getattr(keyboards, kb_name, None)
        if kb_func:
            params = signature(kb_func).parameters
            kb = kb_func(data) if len(params) == 1 else kb_func()
    elif callable(kb_name):
        kb = kb_name()

    # Отправка вопроса (с фото или без)
    if cfg.get("photo_path"):
        await obj.answer_photo(
            types.FSInputFile(path=cfg["photo_path"](data)),
            caption=cfg["ask"],
            reply_markup=kb
        )
    else:
        await obj.answer(cfg["ask"], reply_markup=kb)


async def _send_summary(obj: types.CallbackQuery | types.Message, state: FSMContext):
    data = await state.get_data()
    summary = (
        f"Вот что я записал:\n\n"
        f"• Пол: {'Мужской' if data['sex']=='M' else 'Женский'}\n"
        f"• Рост: {data['height_cm']} см\n"
        f"• Вес: {data['weight_kg']} кг\n"
        f"• Процент жира: {data['body_fat_pct']}%\n"
        f"• Физиологические особенности: {data['health_issues']}\n"
        f"• Дата рождения: {data['birth_date']}\n\n"
        "Всё верно? 😊"
    )
    if isinstance(obj, types.CallbackQuery):
        await obj.message.answer(summary, reply_markup=keyboards.confirm_kb())
        await obj.answer()
    else:
        await obj.answer(summary, reply_markup=keyboards.confirm_kb())

    await state.update_data(editing_field=None)
    await state.set_state(RegistrationStates.confirmation)


async def _start_registration_flow(message: types.Message, state: FSMContext):
    """
    Универсальный запуск воронки: сброс FSM и первый вопрос.
    """
    await state.clear()
    first_key = FIELD_CONFIG[0]["key"]
    await _ask_field(message, state, first_key)
    await state.set_state(CONFIG_BY_KEY[first_key]["state"])


async def cmd_start(message: types.Message, state: FSMContext):
    svc = UserService(message.from_user.id)
    exists = svc.exists()
    svc.close()

    if exists:
        await message.answer(
            "Привет снова! 😊\n"
            "Рад тебя видеть — мы уже знакомы.",
            reply_markup=MenuService(message.from_user.id).get_main_menu_markup()
        )
        return

    # Новый пользователь: удаляем старую клавиатуру и показываем приветствие
    await state.clear()
    await message.answer("Привет! Рад тебя видеть! 👋", reply_markup=types.ReplyKeyboardRemove())
    await message.answer(
        "Я — GymMy, твой помощник в тренировках. Подскажу, как начать, "
        "помогу с программой, поддержу, когда будет сложно, и не дам тебе сдаться 💪\n\n"
        "Кстати, если хочешь — рассчитаю и твою суточную норму калорий️. "
        "Это поможет достигать результата ещё быстрее 🍽️\n\n"
        "Давай вместе сделаем первый шаг — расскажи немного о себе, "
        "и я соберу тренировочный план, который подойдёт именно тебе."
    )
    await _start_registration_flow(message, state)


async def generic_callback_handler(callback: types.CallbackQuery, state: FSMContext):
    cur = await state.get_state()
    _, state_name = cur.split(":", 1)
    key = STATE_TO_KEY[getattr(RegistrationStates, state_name)]
    cfg = CONFIG_BY_KEY[key]

    raw = cfg["parse"](callback.data)
    valid, err = cfg["validate"](raw)
    if not valid:
        return await callback.answer(err, show_alert=True)

    await state.update_data(**{key: cfg["transform"](raw)})
    data = await state.get_data()
    if data.get("editing_field") == key:
        return await _send_summary(callback, state)

    next_key = cfg["next"]
    await _ask_field(callback.message, state, next_key)
    await state.set_state(CONFIG_BY_KEY[next_key]["state"])
    await callback.answer()


async def generic_message_handler(message: types.Message, state: FSMContext):
    cur = await state.get_state()
    if not cur:
        return
    _, state_name = cur.split(":", 1)
    key = STATE_TO_KEY[getattr(RegistrationStates, state_name)]
    cfg = CONFIG_BY_KEY[key]

    if cfg["type"] == "callback":
        return await message.answer(cfg.get("manual_error", "Пожалуйста, выбери кнопкой."))

    valid, err = cfg["validate"](message.text)
    if not valid:
        return await message.answer(err)

    await state.update_data(**{key: cfg["transform"](message.text)})
    data = await state.get_data()

    if key == "health_issues" and data.get("editing_field") is None:
        await message.answer("Ага, обязательно учту это при планировании 😊")

    if data.get("editing_field") == key:
        return await _send_summary(message, state)

    next_key = cfg["next"]
    if next_key:
        await _ask_field(message, state, next_key)
        await state.set_state(CONFIG_BY_KEY[next_key]["state"])
    else:
        await _send_summary(message, state)


async def confirmation_chosen(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    svc = UserService(callback.from_user.id)

    if callback.data == "confirm_yes":
        svc.get_or_create_profile(
            sex=data["sex"],
            height_cm=data["height_cm"],
            weight_kg=data["weight_kg"],
            body_fat_pct=data["body_fat_pct"],
            health_issues=data["health_issues"],
            birth_date=data["birth_date"],
        )

        # Профиль
        await callback.message.answer(
            "🎉 Супер! Твой профиль сохранён!",
            reply_markup=MenuService(callback.message.from_user.id).get_main_menu_markup()
        )

        # Тарифы (только если нет подписки)
        sub_svc = SubscriptionService(callback.from_user.id)
        try:
            if not sub_svc.has_active():
                tariffs_text = (
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
                await callback.message.answer(
                    tariffs_text,
                    parse_mode="Markdown",
                    reply_markup=keyboards.tariffs_kb()
                )

                # Очищаем состояние и показываем главное меню
                await state.clear()
                await callback.message.answer(
                    "Или можно остаться на бесплатной версии и пользоваться ботом через кнопки ниже 👇",
                    reply_markup=MenuService(callback.message.from_user.id).get_main_menu_markup()
                )
        finally:
            sub_svc.close()

        await state.clear()

    else:
        await callback.message.answer(
            "Что именно хочешь поменять?",
            reply_markup=keyboards.edit_field_kb()
        )

    svc.close()


async def edit_field_chosen(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    field = callback.data.split("_", 1)[1]
    await state.update_data(editing_field=field)
    await _ask_field(callback.message, state, field)
    await state.set_state(CONFIG_BY_KEY[field]["state"])


async def update_data(message: types.Message, state: FSMContext):
    svc = UserService(message.from_user.id)
    if not svc.exists():
        await message.answer(
            "Я пока не знаю твоих данных. Сначала заполни профиль командой /start."
        )
        svc.close()
        return
    svc.close()

    # очищаем Reply-клавиатуру и заново запускаем flow
    await message.answer("Обновим твои данные:", reply_markup=types.ReplyKeyboardRemove())
    await _start_registration_flow(message, state)


def register_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, CommandStart())

    for cfg in FIELD_CONFIG:
        if cfg["type"] in ("callback", "both"):
            prefix = cfg.get("prefix", cfg["key"])
            dp.callback_query.register(
                generic_callback_handler,
                StateFilter(cfg["state"]),
                F.data.startswith(f"{prefix}_"),
            )

    all_states = [cfg["state"] for cfg in FIELD_CONFIG]
    dp.message.register(generic_message_handler, StateFilter(*all_states))

    dp.callback_query.register(
        confirmation_chosen,
        StateFilter(RegistrationStates.confirmation),
        F.data.startswith("confirm_"),
    )
    dp.callback_query.register(
        edit_field_chosen,
        StateFilter(RegistrationStates.confirmation),
        F.data.startswith("edit_"),
    )

    dp.message.register(update_data, F.text == "✍️ Обновить данные")
