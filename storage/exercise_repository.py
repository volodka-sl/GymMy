from storage.db import SessionLocal
from storage.models import Exercise
from typing import List, Optional


class ExerciseRepository:
    def __init__(self):
        self._session = SessionLocal()

    def get_muscle_groups(self) -> List[str]:
        # возвращает список уникальных primary_muscle
        rows = (
            self._session
            .query(Exercise.primary_muscle)
            .distinct()
            .all()
        )
        return [r[0] for r in rows]

    def get_levels_for_muscle(self, muscle: str) -> List[str]:
        # возвращает список уникальных уровней (difficulty) для данной мышцы
        rows = (
            self._session
            .query(Exercise.difficulty)
            .filter(Exercise.primary_muscle == muscle)
            .distinct()
            .all()
        )
        return [r[0].value for r in rows]

    def get_exercises(self, muscle: str, level) -> List[Exercise]:
        # возвращает все упражнения по мышце и уровню сложности
        return (
            self._session
            .query(Exercise)
            .filter(
                Exercise.primary_muscle == muscle,
                Exercise.difficulty == level
            )
            .all()
        )

    def get_exercise_by_name(self, name: str) -> Optional[Exercise]:
        # поиск по точному названию
        return (
            self._session
            .query(Exercise)
            .filter(Exercise.name == name)
            .one_or_none()
        )

    def get_exercise_by_id(self, exercise_id: int) -> Optional[Exercise]:
        # поиск по первичному ключу
        return self._session.get(Exercise, exercise_id)

    def close(self):
        self._session.close()
