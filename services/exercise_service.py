# services/exercise_service.py

from typing import List, Optional, Union
from storage.exercise_repository import ExerciseRepository
from storage.models import DifficultyLevel, Exercise


class ExerciseService:
    def __init__(self):
        self._repo = ExerciseRepository()

    def list_muscles(self) -> List[str]:
        return self._repo.get_muscle_groups()

    def list_levels(self, muscle: str) -> List[DifficultyLevel]:
        # возвращаем объекты Enum, а в клавиатуре берём .value или .name
        return [DifficultyLevel(l) for l in self._repo.get_levels_for_muscle(muscle)]

    def list_exercises(self, muscle: str, level: DifficultyLevel) -> List[Exercise]:
        return self._repo.get_exercises(muscle, level)

    def list_exercises_by_level(self, level: Union[DifficultyLevel, str]) -> List[Exercise]:
        """
        Возвращает все упражнения заданного уровня сложности, независимо от группы мышц.
        """
        # нормализуем level к enum
        lvl = level if isinstance(level, DifficultyLevel) else DifficultyLevel(level)
        # используем сессию репозитория для общего запроса
        session = self._repo._session
        return (
            session
            .query(Exercise)
            .filter(Exercise.difficulty == lvl)
            .all()
        )

    def get_detail(self, name: str) -> Optional[Exercise]:
        return self._repo.get_exercise_by_name(name)

    def get_detail_by_id(self, exercise_id: int) -> Optional[Exercise]:
        return self._repo.get_exercise_by_id(exercise_id)

    def close(self):
        self._repo.close()
