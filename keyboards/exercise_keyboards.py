from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from storage.models import DifficultyLevel, Exercise

def muscles_kb(muscles: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # “Отменить” → single button in first row
    builder.button(text="❌ Отменить", callback_data="exercise_cancel")
    # then 2 per row
    for m in muscles:
        builder.button(text=m, callback_data=f"muscle_choice:{m}")
    builder.adjust(1, 2)        # first row: 1 button; after: 2 per row
    return builder.as_markup()

def levels_kb(levels: list[DifficultyLevel]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # “Назад” → first row
    builder.button(text="◀️ Назад", callback_data="back_to_muscle")
    labels = {
        DifficultyLevel.easy:     "🍋 Лёгкий",
        DifficultyLevel.medium:   "🐣 Средний",
        DifficultyLevel.advanced: "🌪 Продвинутый",
    }
    # then 2 per row
    for lvl in levels:
        builder.button(text=labels[lvl], callback_data=f"level_{lvl.value}")
    builder.adjust(1, 2)
    return builder.as_markup()

def exercises_kb(exs: list[Exercise]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # “Назад” → first row
    builder.button(text="◀️ Назад", callback_data="back_to_level")
    # then one exercise per row
    for ex in exs:
        builder.button(text=ex.name, callback_data=f"exercise:{ex.exercise_id}")
    builder.adjust(1, 1)        # all rows: single button
    return builder.as_markup()
