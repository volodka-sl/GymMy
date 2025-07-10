# storage/reminder_text_repository.py

from datetime import date
from sqlalchemy.orm import Session
from storage.db import SessionLocal
from storage.models import ReminderText, ReminderGender

class ReminderTextRepository:
    """
    CRUD для таблицы reminder_text.
    """

    def __init__(self):
        self._session: Session = SessionLocal()

    def get_by_date_and_gender(self, day: date, gender: ReminderGender) -> ReminderText | None:
        return (
            self._session
            .query(ReminderText)
            .filter_by(date=day, gender=gender)
            .one_or_none()
        )

    def save(self, day: date, gender: ReminderGender, text: str) -> ReminderText:
        reminder = self.get_by_date_and_gender(day, gender)
        if reminder:
            reminder.text = text
        else:
            reminder = ReminderText(date=day, gender=gender, text=text)
            self._session.add(reminder)
        self._session.commit()
        return reminder

    def delete(self, day: date, gender: ReminderGender):
        reminder = self.get_by_date_and_gender(day, gender)
        if reminder:
            self._session.delete(reminder)
            self._session.commit()

    def close(self):
        self._session.close()
