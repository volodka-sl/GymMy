from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def default_menu() -> ReplyKeyboardMarkup:
    # Для бесплатных добавляем кнопку «Premium»
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="⭐ Premium")
            ],
            [
                KeyboardButton(text="✍️ Обновить данные"),
                KeyboardButton(text="📚 База упражнений")
            ],
        ],
        resize_keyboard=True,
    )

def premium_menu() -> ReplyKeyboardMarkup:
    # Меню для активных подписчиков без кнопки «Premium»
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="💬 Задать вопрос")
            ],
            [
                KeyboardButton(text="🏋️ Мои тренировки")
            ],
            [
                KeyboardButton(text="✍️ Обновить данные"),
                KeyboardButton(text="📚 База упражнений")
            ],
        ],
        resize_keyboard=True,
    )
