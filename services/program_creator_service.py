# services/program_creator_service.py

import json
from datetime import date
from sqlalchemy import func

from storage.db import SessionLocal
from storage.models import (
    ProgramTemplate,
    TemplateExercise,
    UserProgram,
    UserProgramSchedule,
    Exercise,
    DifficultyLevel
)
from services.plan_chat_service import PlanChatService
from services.user_service import UserService
from services.exercise_service import ExerciseService

LEVELS_RU = {
    "easy": "Лёгкий",
    "medium": "Средний",
    "advanced": "Продвинутый"
}
DAYS_RU = [
    "Понедельник", "Вторник", "Среда", "Четверг",
    "Пятница", "Суббота", "Воскресенье"
]

class ProgramCreatorService:
    def __init__(self, telegram_id: int):
        self._session = SessionLocal()
        self._chat = PlanChatService()
        self._user_id = telegram_id

    async def generate_and_save_plan(self, level: str, comment: str, day_of_week: str) -> None:
        user = UserService(self._user_id).get_profile()
        exercises = ExerciseService().list_exercises_by_level(level)

        user_payload = {
            "sex":           user.sex,
            "height_cm":     user.height_cm,
            "weight_kg":     float(user.weight_kg),
            "body_fat_pct":  user.body_fat_pct,
            "health_issues": user.health_issues,
            "wish": comment,
            "day_of_week": day_of_week
        }
        exercises_payload = [
            {"name": ex.name, "difficulty": ex.difficulty.value}
            for ex in exercises
        ]

        result = await self._chat.generate_plan(user_payload, exercises_payload)
        plan_name = result["name"]
        level_ru = LEVELS_RU.get(level, level)
        full_name = f"{plan_name} ({level_ru}, {day_of_week})"
        plan = result["plan"]

        tpl = ProgramTemplate(
            name=full_name,
            difficulty=DifficultyLevel(level),
            created_by="chatgpt"
        )
        self._session.add(tpl)
        self._session.commit()
        self._session.refresh(tpl)

        day_of_week_num = DAYS_RU.index(day_of_week) + 1  # 1–7
        schedule = UserProgramSchedule(
            template_id=tpl.template_id,
            day_of_week=day_of_week_num
        )
        self._session.add(schedule)

        try:
            for idx, item in enumerate(plan):
                name = item["name"].strip().lower()
                ex = (
                    self._session
                    .query(Exercise)
                    .filter(func.lower(Exercise.name) == name)
                    .first()
                )
                if ex is None:
                    raise ValueError(f"Упражнение '{item['name']}' не найдено в exercise. Проверьте наполнение БД или промт к ChatGPT.")
                te = TemplateExercise(
                    template_id=tpl.template_id,
                    exercise_id=ex.exercise_id,
                    sort_order=idx,
                    sets=item["sets"],
                    reps=item["reps"]
                )
                self._session.add(te)
        except Exception as e:
            self._session.rollback()
            self._session.close()
            raise ValueError(str(e))

        user_record = UserService(self._user_id)._repo.get_by_telegram_id(self._user_id)
        up = UserProgram(
            user_id=user_record.user_id,
            template_id=tpl.template_id,
            start_date=date.today()
        )
        self._session.add(up)
        self._session.commit()
        self._session.close()

    async def generate_and_save_full_plan(self, level: str, comment: str, days_text: str) -> None:
        """
        Генерирует и сохраняет недельный план (каждый день — отдельная программа с тематичным названием).
        """
        user = UserService(self._user_id).get_profile()
        exercises = ExerciseService().list_exercises_by_level(level)

        user_payload = {
            "sex": user.sex,
            "height_cm": user.height_cm,
            "weight_kg": float(user.weight_kg),
            "body_fat_pct": user.body_fat_pct,
            "health_issues": user.health_issues,
            "wish": comment,
            "days_text": days_text
        }
        exercises_payload = [
            {"name": ex.name, "difficulty": ex.difficulty.value}
            for ex in exercises
        ]

        plan_list = await self._chat.generate_full_plan(user_payload, exercises_payload)

        # Валидация всех тренировок заранее
        all_errors = []
        for day_plan in plan_list:
            if "day" not in day_plan or not day_plan["day"]:
                all_errors.append("Не найден день недели у одной из тренировок.")
                continue
            if "exercises" not in day_plan or not isinstance(day_plan["exercises"], list) or not day_plan["exercises"]:
                all_errors.append(f"В дне {day_plan.get('day', '?')} нет упражнений.")
                continue
            seen = set()
            for idx, item in enumerate(day_plan["exercises"]):
                name = item.get("name", "").strip().lower()
                if name in seen:
                    all_errors.append(f"В дне '{day_plan['day']}' дублируется упражнение '{item['name']}'!")
                    continue
                seen.add(name)
                ex = (
                    self._session
                    .query(Exercise)
                    .filter(func.lower(Exercise.name) == name)
                    .first()
                )
                if ex is None:
                    all_errors.append(
                        f"В дне '{day_plan.get('day', '?')}' упражнение '{item.get('name', '')}' не найдено в базе.")
        if all_errors:
            self._session.close()
            raise ValueError("; ".join(all_errors))

        user_record = UserService(self._user_id)._repo.get_by_telegram_id(self._user_id)

        # Для каждого дня — отдельная программа с уникальным названием
        for day_plan in plan_list:
            day_name = day_plan["day"]
            plan_name = day_plan.get("name") or "Тренировка"
            level_ru = LEVELS_RU.get(level, level)
            full_name = f"{plan_name} ({level_ru}, {day_name})"
            tpl = ProgramTemplate(
                name=full_name,
                difficulty=DifficultyLevel(level),
                created_by="chatgpt"
            )
            self._session.add(tpl)
            self._session.commit()
            self._session.refresh(tpl)

            # Привязка к дню недели
            try:
                day_num = DAYS_RU.index(day_name) + 1
            except Exception:
                day_num = None
            if day_num:
                schedule = UserProgramSchedule(
                    template_id=tpl.template_id,
                    day_of_week=day_num
                )
                self._session.add(schedule)

            for idx, item in enumerate(day_plan["exercises"]):
                name = item["name"].strip().lower()
                ex = (
                    self._session
                    .query(Exercise)
                    .filter(func.lower(Exercise.name) == name)
                    .first()
                )
                te = TemplateExercise(
                    template_id=tpl.template_id,
                    exercise_id=ex.exercise_id,
                    sort_order=idx,
                    sets=item["sets"],
                    reps=item["reps"]
                )
                self._session.add(te)

            up = UserProgram(
                user_id=user_record.user_id,
                template_id=tpl.template_id,
                start_date=date.today()
            )
            self._session.add(up)
            self._session.commit()
        self._session.close()
