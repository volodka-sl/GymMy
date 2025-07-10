from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def chat_back_kb() -> ReplyKeyboardMarkup:
    """
    Клавиатура с одной кнопкой «◀️ Назад».
    Используется в диалоге с ИИ.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="◀️ Назад")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
