# services/user_program_view_service.py

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from storage.user_program_repository import UserProgramRepository
from storage.template_exercise_repository import TemplateExerciseRepository
from storage.exercise_repository import ExerciseRepository
from storage.models import DifficultyLevel

LEVELS_RU = {
    "easy": "Лёгкий",
    "medium": "Средний",
    "advanced": "Продвинутый"
}

class UserProgramViewService:
    def __init__(self, telegram_id: int):
        self._user_program_repo = UserProgramRepository()
        self._template_ex_repo = TemplateExerciseRepository()
        self._exercise_repo = ExerciseRepository()
        self._telegram_id = telegram_id

    def get_user_program_detail(self, user_program_id: int):
        user_program = self._user_program_repo.get(user_program_id)
        if not user_program:
            return "Тренировка не найдена.", None

        template = user_program.template
        level_value = template.difficulty.value if isinstance(template.difficulty, DifficultyLevel) else str(template.difficulty)
        level_ru = LEVELS_RU.get(level_value, str(template.difficulty))

        text = [
            f"🏋️ Тренировка: {template.name}",
            f"Дата создания: {user_program.start_date.strftime('%d.%m.%Y') if user_program.start_date else '-'}",
            f"Уровень: {level_ru}",
            "",
            "<b>Упражнения:</b>"
        ]

        template_exs = self._template_ex_repo.list_by_template(template.template_id)
        # Сначала "Назад", потом "Удалить", потом — подробнее по каждому упражнению
        buttons = [
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_workouts_list")],
            [InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_program:{user_program.user_program_id}")]
        ]
        for idx, t_ex in enumerate(template_exs, 1):
            ex = self._exercise_repo.get_exercise_by_id(t_ex.exercise_id)
            line = f"{idx}. {ex.name}: {t_ex.sets}×{t_ex.reps}"
            text.append(line)
            buttons.append([InlineKeyboardButton(text=f"🔎 Подробнее: {ex.name}",
                                                 callback_data=f"exercise_detail:{ex.exercise_id}")])
        markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        return "\n".join(text), markup
