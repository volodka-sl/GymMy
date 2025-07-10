# storage/program_template_repository.py

from storage.db import SessionLocal
from storage.models import ProgramTemplate
from typing import Optional, List


class ProgramTemplateRepository:
    """
    Репозиторий для работы с таблицей program_template.
    """

    def __init__(self):
        self._session = SessionLocal()

    def add(self, template: ProgramTemplate) -> ProgramTemplate:
        """
        Сохраняет новый шаблон программы в БД.
        Возвращает объект с заполненным template_id.
        """
        self._session.add(template)
        self._session.commit()
        self._session.refresh(template)
        return template

    def get(self, template_id: int) -> Optional[ProgramTemplate]:
        """
        Возвращает шаблон программы по ID или None.
        """
        return (
            self._session
                .query(ProgramTemplate)
                .filter(ProgramTemplate.template_id == template_id)
                .one_or_none()
        )

    def list_by_difficulty(self, difficulty: str) -> List[ProgramTemplate]:
        """
        Список шаблонов по уровню сложности.
        """
        return (
            self._session
                .query(ProgramTemplate)
                .filter(ProgramTemplate.difficulty == difficulty)
                .all()
        )

    def close(self):
        self._session.close()
