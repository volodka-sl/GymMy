# handlers/training_reminder.py

from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from states import ChatStates
from keyboards.chat_keyboards import chat_back_kb
from services.chat_service import ChatService
from services.main_menu_service import MenuService

router = Router()

@router.message(StateFilter(ChatStates.chatting))
async def reminder_chat_message(message: Message, state: FSMContext):
    # Пользователь отвечает на напоминание, отправляем его текст в Gymmy
    history = (await state.get_data()).get("history", [])
    chat_svc = ChatService()
    # Готовим формат для истории сообщений (list of dicts с role/content)
    messages = history + [{"role": "user", "content": message.text}]
    answer = await chat_svc.get_response(messages)
    # Добавляем ответ в историю
    history = messages + [{"role": "assistant", "content": answer}]
    await state.update_data(history=history)
    await message.answer(answer, reply_markup=chat_back_kb())

@router.callback_query(lambda c: c.data == "chat_back", StateFilter(ChatStates.chatting))
async def chat_back_cb(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    markup = MenuService(callback.from_user.id).get_main_menu_markup()
    await callback.message.answer("Вы в главном меню 🫡", reply_markup=markup)
