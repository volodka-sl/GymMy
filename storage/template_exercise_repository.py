# storage/template_exercise_repository.py

from storage.db import SessionLocal
from storage.models import TemplateExercise
from typing import List


class TemplateExerciseRepository:
    """
    Репозиторий для работы с таблицей template_exercise.
    """

    def __init__(self):
        self._session = SessionLocal()

    def add_all(self, exercises: List[TemplateExercise]) -> None:
        """
        Сохраняет список TemplateExercise в БД.
        """
        self._session.add_all(exercises)
        self._session.commit()

    def list_by_template(self, template_id: int) -> List[TemplateExercise]:
        """
        Возвращает все TemplateExercise для заданного template_id, упорядоченные по sort_order.
        """
        return (
            self._session
                .query(TemplateExercise)
                .filter(TemplateExercise.template_id == template_id)
                .order_by(TemplateExercise.sort_order)
                .all()
        )

    def delete_by_template(self, template_id: int) -> None:
        """
        Удаляет все записи TemplateExercise для заданного шаблона.
        """
        (
            self._session
                .query(TemplateExercise)
                .filter(TemplateExercise.template_id == template_id)
                .delete(synchronize_session=False)
        )
        self._session.commit()

    def close(self):
        self._session.close()
