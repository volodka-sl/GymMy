from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_workout_keyboard(programs=None):
    """
    Клавиатура: отмена, создать тренировку, создать план, список программ.
    """
    buttons = [
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_creation")],
        [InlineKeyboardButton(text="🏋️ Создать тренировку", callback_data="create_workout")],
        [InlineKeyboardButton(text="📅 Создать план", callback_data="plan_create")],
    ]
    if programs:
        for prog in programs:
            buttons.append([
                InlineKeyboardButton(
                    text=prog.template.name,
                    callback_data=f"workout_{prog.user_program_id}"
                )
            ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def level_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_workouts")],
        [InlineKeyboardButton(text="🍋 Лёгкий", callback_data="level_easy")],
        [InlineKeyboardButton(text="🐣 Средний", callback_data="level_medium")],
        [InlineKeyboardButton(text="🌪 Продвинутый", callback_data="level_advanced")],
    ])
