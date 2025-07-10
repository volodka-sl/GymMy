# handlers/chat.py

from aiogram import Router, F
from aiogram.filters.state import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from services.chat_service import ChatService
from services.subscription_service import SubscriptionService
from services.main_menu_service import MenuService
from keyboards.chat_keyboards import chat_back_kb
from states import ChatStates

from storage.user_repository import UserRepository  # <-- добавили для чтения профиля

router = Router()
chat_svc = ChatService()


@router.message(F.text == "💬 Задать вопрос")
async def start_chat(message: Message, state: FSMContext):
    """
    Точка входа в диалог с ChatGPT.
    Разрешаем только премиум-пользователям.
    """
    tg_id = message.from_user.id
    sub_svc = SubscriptionService(tg_id)
    try:
        if not sub_svc.has_active():
            await message.answer(
                "❗️ Этот раздел доступен только пользователям с Premium-подпиской.",
                reply_markup=MenuService(tg_id).get_main_menu_markup(),
            )
            return
    finally:
        sub_svc.close()

    # Устанавливаем FSM-состояние chatting
    await state.set_state(ChatStates.chatting)
    # Инициализируем пустую историю сообщений
    await state.update_data(history=[])
    await message.answer(
        "❓ Задай любой вопрос — я отвечу!",
        reply_markup=chat_back_kb()
    )


@router.message(StateFilter(ChatStates.chatting), F.text == "◀️ Назад")
async def cancel_chat(message: Message, state: FSMContext):
    """
    Отмена чата — возвращаемся в меню.
    """
    await state.clear()
    await message.answer(
        "🔙 Возврат в главное меню.",
        reply_markup=MenuService(message.from_user.id).get_main_menu_markup()
    )


@router.message(StateFilter(ChatStates.chatting), ~F.text.in_({"◀️ Назад"}))
async def process_chat(message: Message, state: FSMContext):
    """
    Обрабатываем любой текст, присланный в состоянии chatting, спрашиваем ChatGPT.
    Добавляем профиль пользователя и историю диалога.
    """
    thinking = await message.answer("⚡️ Думаю…")

    # 1) Получаем профиль из БД
    user_repo = UserRepository()
    user = user_repo.get_by_telegram_id(message.from_user.id)
    user_repo.close()
    if not user:
        await thinking.delete()
        return await message.answer(
            "❗️ Не удалось найти ваш профиль. Пожалуйста, зарегистрируйтесь заново.",
            reply_markup=MenuService(message.from_user.id).get_main_menu_markup()
        )

    # 2) Формируем строку с полями профиля
    profile_parts = []
    for col in user.__table__.columns:
        name = col.name
        if name in ("user_id", "telegram_id", "created_at", "tz_offset"):
            continue
        val = getattr(user, name)
        profile_parts.append(f"{name.replace('_', ' ').title()}: {val}")
    profile_str = "; ".join(profile_parts)

    # 3) Собираем сообщения для OpenAI: сначала профиль, потом история, потом новый ввод
    system_msg = {"role": "system", "content": f"Профиль пользователя: {profile_str}"}
    data = await state.get_data()
    history = data.get("history", [])
    user_msg = {"role": "user", "content": message.text}
    messages = [system_msg] + history + [user_msg]

    # 4) Запрашиваем у ChatGPT
    answer = await chat_svc.get_response(messages)

    # 5) Обновляем историю в FSMContext
    new_history = history + [user_msg, {"role": "assistant", "content": answer}]
    await state.update_data(history=new_history)

    # 6) Отправляем ответ пользователю
    await thinking.delete()
    await message.answer(
        answer,
        reply_markup=chat_back_kb(),
        parse_mode="HTML"
    )
